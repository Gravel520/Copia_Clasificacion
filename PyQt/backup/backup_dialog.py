'''
Script en Python.
'''

import os
import json
import subprocess
import config_manager

from config_paths import (
    ruta_adb, ruta_movil, get_ruta_backup
)

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QTextEdit, QProgressBar, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal

from backup.hash_indexer import calcular_hash
from backup.hash_indexer_adb import (
    adb_listar_archivos, adb_descargar_archivo,
    calcular_hash_local
)
from backup.backup_restore import restaurar_desde_json
from backup.backup_incremental import generar_backup_incremental, guardar_diff
from backup.backup_audit import nueva_auditoria, registrar_evento, crear_evento
from backup.backup_simulation import simular_restauracion

PASO_CREAR_INDICE = 2
PASO_RESTAURAR = 3
PASO_BACKUP = 4

class BackupDialog(QDialog):
    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._restaurados = False
        self.paso_actual = None
        self.style_normal = "background-color: none;"
        self.style_resaltado = "background-color: #4CAF50;"

        self.setWindowTitle("Gestión de Backup")
        self.resize(500, 600)

        self.rutas_origen = []
        self.indice_hashes = {}
        self.autidoria = nueva_auditoria()

        layout = QVBoxLayout(self)

        botones_rutas = QHBoxLayout()
        self.btn_add = QPushButton("Añadir Ruta PC")
        self.btn_add_movil = QPushButton("Añadir móvil")
        self.btn_del = QPushButton("Eliminar Ruta")
        botones_rutas.addWidget(self.btn_add)
        botones_rutas.addWidget(self.btn_add_movil)
        botones_rutas.addWidget(self.btn_del)

        layout.addLayout(botones_rutas)

        # Lista de rutas origen
        self.lista_rutas = QListWidget()
        layout.addWidget(self.lista_rutas)

        self.btn_add.clicked.connect(self.anadir_ruta)
        self.btn_add_movil.clicked.connect(self.add_movil_adb)
        self.btn_del.clicked.connect(self.borrar_ruta)

        # Botones de acciones
        acciones = QHBoxLayout()
        self.btn_indice = QPushButton("Generar índice")
        self.btn_restaurar = QPushButton("Restaurar")
        self.btn_incremental = QPushButton("Generar backup incremental")
        acciones.addWidget(self.btn_indice)
        acciones.addWidget(self.btn_restaurar)
        acciones.addWidget(self.btn_incremental)

        layout.addLayout(acciones)

        self.btn_indice.clicked.connect(self.generar_indice)
        self.btn_restaurar.clicked.connect(self.restaurar)
        self.btn_incremental.clicked.connect(self.backup_incremental)

        # Barra de progreso
        self.progreso = QProgressBar(self)
        self.progreso.setValue(0)
        layout.addWidget(self.progreso)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.log)

        # Botón cerrar
        cerrar = QHBoxLayout()
        cerrar.setContentsMargins(10, 10, 10, 10)
        cerrar.setSpacing(5)
        cerrar.setAlignment(Qt.AlignRight)
        self.btn_simular = QPushButton("Simular Restauración")
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_simular.clicked.connect(self.simular_restauracion)
        self.btn_cerrar.clicked.connect(self.close)
        cerrar.addWidget(self.btn_simular)
        cerrar.addStretch()
        cerrar.addWidget(self.btn_cerrar)
        layout.addLayout(cerrar)

        self.setLayout(layout)

        self.actualizar_botones()

    def closeEvent(self, a0):
        super().closeEvent(a0)

        if self._restaurados:
            self._reset_estado_mapa()

        self.cerrado.emit()

    def _reset_estado_mapa(self):
        config_manager.settings.setValue("Estado/mapa_generado", "False")
        config_manager.settings.sync()
        
    def anadir_ruta(self):
        ruta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if ruta:
            self.rutas_origen.append(ruta)
            self.lista_rutas.addItem(ruta)

        self.paso_actual = PASO_CREAR_INDICE
        self.actualizar_botones()

    def borrar_ruta(self):
        item = self.lista_rutas.currentItem()
        if not item:
            return
        
        ruta = item.text()

        # Si es una ruta ADB, quitar el prefijo
        if ruta.startswith("[ADB] "):
            ruta_real = ruta.replace("[ADB] ", "")
        else:
            ruta_real = ruta

        # Eliminar de la lista interna
        if ruta_real in self.rutas_origen:
            self.rutas_origen.remove(ruta_real)
        else:
            # Mostrar información útil para depuración
            self.log.append(f"Advertencia: la ruta '{ruta_real}' no estaba en rutas_origen.")

        self.lista_rutas.takeItem(self.lista_rutas.row(item))

        if len(self.lista_rutas) == 0:
            self.paso_actual = None
            self.actualizar_botones()

    def generar_indice(self):
        self.log.append("Generando índice de hashes...")

        rutas_pc = [r for r in self.rutas_origen if not r.startswith("adb://")]
        rutas_adb_movil = [r for r in self.rutas_origen if r.startswith("adb://")]

        # Contar archivos.
        total_pc = self.contar_archivos_pc(rutas_pc)
        total_adb = self.contar_archivos_adb(rutas_adb_movil)
        total = total_pc + total_adb

        self.iniciar_progreso(total)

        # Indexar PC
        indice_pc = {}
        for raiz in rutas_pc:
            for r, _, archivos in os.walk(raiz):
                for nombre in archivos:
                    ruta = os.path.join(r, nombre)
                    try:
                        h = calcular_hash(ruta)
                    except:
                        continue

                    indice_pc.setdefault(h, []).append(ruta)
                    self.avanzar_progreso()

        # Indexar ADB
        indice_adb = {}
        for raiz in rutas_adb_movil:
            serial = rutas_adb_movil.split("adb://")[1].split("/")[0]
            archivos = adb_listar_archivos(rutas_adb_movil)

            for ruta_remota in archivos:
                try:
                    ruta_tmp = adb_descargar_archivo(serial, ruta_remota)
                    h = calcular_hash_local(ruta_tmp)
                    os.remove(ruta_tmp)
                except:
                    continue

                indice_adb.setdefault(h, []).append(f"{serial}:{ruta_remota}")
                self.avanzar_progreso()

        # Unir ambos índices
        self.indice_hashes = {**indice_pc}

        for h, rutas in indice_adb.items():
            if h not in self.indice_hashes:
                self.indice_hashes.setdefault(h, []).extend(rutas)

        self.finalizar_progreso()
        self.log.append(f"Índice generado: {len(self.indice_hashes)} archivos")

        registrar_evento(self.autidoria, crear_evento("indice_generado", {
            "total": len(self.indice_hashes)
        }))

        self.paso_actual = PASO_RESTAURAR
        self.actualizar_botones()

    def restaurar(self):
        data_json_backup = self.cargar_json_backup()
        if data_json_backup is None:
            return

        self.log.append("Restaurando archivos faltantes...")

        # Obtener items para progreso
        items = data_json_backup.get("clasificados", {}).get("items", [])
        total_items = len(items)
        self.iniciar_progreso(total_items)

        # Llamada al módulo externo
        resultado = restaurar_desde_json(data_json_backup, self.indice_hashes)

        # Generamos el mapa si se han restaurado archivos.
        self._restaurados = len(resultado["restaurados"]) > 0

        # Avanzar la barra por cada items del JSON
        for _ in items:
            self.avanzar_progreso()

        self.finalizar_progreso()

        # Mostrar resultados
        if resultado["restaurados"]:
            self.log.append("\nArchivos restaurados:")
            for r in resultado["restaurados"]:
                self.log.append(f"- {r}")
                registrar_evento(self.autidoria, crear_evento("restaurado", {"ruta": r}))

        if resultado["no_encontrados"]:
            self.log.append("\nArchivos no encontrados:")
            for h in resultado["no_encontrados"]:
                self.log.append(f"- {h}")
                registrar_evento(self.autidoria, crear_evento("perdido", {"hash": h}))

        if "ya_clasificados" in resultado and resultado["ya_clasificados"]:
            self.log.append("\nArchivos ya clasificados:")
            for c in resultado["ya_clasificados"]:
                self.log.append(f"- {c}")
                registrar_evento(self.autidoria, crear_evento("clasificado", {"hash": c}))

        self.log.append("Restauración completada.")
        self.ajustar_ancho_por_log()

        self.paso_actual = PASO_BACKUP
        self.actualizar_botones()

    def backup_incremental(self):
        ruta_old, _ = QFileDialog.getOpenFileName(self, "JSON anterior", "", "JSON (*.json)")
        ruta_new, _ = QFileDialog.getOpenFileName(self, "JSON actual", "", "JSON (*.json)")

        if not ruta_old or not ruta_new:
            return
        
        with open(ruta_old, "r", encoding="utf-8") as f:
            old = json.load(f)
        with open(ruta_new, "r", encoding="utf-8") as f:
            new = json.load(f)

        diff = generar_backup_incremental(old, new)
        
        ruta_salida, _ = QFileDialog.getSaveFileName(self, "Guardar diff", "", "JSON (*.json)")
        if ruta_salida:
            guardar_diff(diff, ruta_salida)
            self.log.append("Backup incremental generado.")

            registrar_evento(self.autidoria, crear_evento("backup_incremental", {"ruta": ruta_salida}))

        self.paso_actual = PASO_CREAR_INDICE
        self.actualizar_botones()

    def simular_restauracion_item(self, item):
        hash_archivo = item["hash"]
        ruta_destino = item["ruta"]

        resultado = {
            "faltantes": [],
            "recuperables": [],
            "perdidos": [],
            "carpetas_a_crear": [],
            "movimientos": []
        }

        if not os.path.exists(ruta_destino):
            resultado["faltantes"].append(ruta_destino)

            rutas_origen = self.inherits.get(hash_archivo)
            if rutas_origen:
                resultado["recuperables"].append({
                    "hash": hash_archivo,
                    "ruta_destino": ruta_destino,
                    "ruta_origen": rutas_origen[0]
                })
            else:
                resultado["perdidos"].append({
                    "hash": hash_archivo,
                    "ruta_destino": ruta_destino
                })

        carpeta = os.path.dirname(ruta_destino)
        if not os.path.exists(carpeta):
            resultado["carpetas_a_crear"].append(carpeta)

        rutas_origen = self.indice_hashes.get(hash_archivo, [])
        for r in rutas_origen:
            if os.path.exists(r) and r != ruta_destino:
                resultado["movimientos"].append({
                    "hash": hash_archivo,
                    "antes": r,
                    "despues": ruta_destino
                })

        return resultado

    def simular_restauracion(self):
        data_json_backup = self.cargar_json_backup()
        if data_json_backup is None:
            return

        items = data_json_backup.get("clasificados", {}).get("items", [])
        total_items = len(items)

        self.log.append("Simulando restauración...")
        self.iniciar_progreso(total_items)

        resultado = simular_restauracion(data_json_backup, self.indice_hashes)

        # Avanzar la barra por cada item del JSON
        for _ in items:
            self.avanzar_progreso()

        self.finalizar_progreso()

        # Mostrar faltantes
        if resultado["faltantes"]:
            self.log.append("\nArchivos faltantes:")
            for r in resultado["faltantes"]:
                self.log.append(f"- {r}")

        # Mostrar recuperables
        if resultado["recuperables"]:
            self.log.append("\nArchivos recuperables:")
            for item in resultado["recuperables"]:
                self.log.append(f"- {item['ruta_destino']} (desde {item['ruta_origen']})")

        # Mostrar perdidos
        if resultado["perdidos"]:
            self.log.append("\nArchivos perdidos:")
            for item in resultado["perdidos"]:
                self.log.append(f"- {item['ruta_destino']} (hash: {item['hash']})")

        # Carpetas a crear
        if resultado["carpetas_a_crear"]:
            self.log.append("\nCarpetas a crear:")
            for c in resultado["carpetas_a_crear"]:
                self.log.append(f"- {c}")

        # Movimientos detectados
        if resultado["movimientos"]:
            self.log.append("\nMovimientos detectados:")
            for m in resultado["movimientos"]:
                self.log.append(f"- {m['antes']} -> {m['despues']}")

        self.log.append("\nSimulación completada.")
        self.ajustar_ancho_por_log()

        # Registrar auditoría
        registrar_evento(self.autidoria, crear_evento("simulacion_restauracion", resultado))

        self.paso_actual = PASO_RESTAURAR
        self.actualizar_botones()

    def actualizar_botones(self):
        # Paso 1: Añadir ruta y borrar ruta siempre habilitado
        self.btn_add.setEnabled(True)
        self.btn_add_movil.setEnabled(True)
        self.btn_del.setEnabled(True)
        self.btn_add.setStyleSheet(self.style_resaltado)
        self.btn_add_movil.setStyleSheet(self.style_resaltado)
        self.btn_del.setStyleSheet(self.style_resaltado)

        # Paso 2: Crear índice.
        self.btn_indice.setEnabled(self.paso_actual == PASO_CREAR_INDICE)
        self.btn_indice.setStyleSheet(
            self.style_resaltado if self.paso_actual == PASO_CREAR_INDICE else self.style_normal
        )

        # Paso 3: Restaurar.
        self.btn_restaurar.setEnabled(self.paso_actual == PASO_RESTAURAR)
        self.btn_simular.setEnabled(self.paso_actual == PASO_RESTAURAR)
        self.btn_restaurar.setStyleSheet(
            self.style_resaltado if self.paso_actual == PASO_RESTAURAR else self.style_normal
        )
        self.btn_simular.setStyleSheet(
            self.style_resaltado if self.paso_actual == PASO_RESTAURAR else self.style_normal
        )

        # Paso 4: Generar backup.
        self.btn_incremental.setEnabled(self.paso_actual == PASO_BACKUP)
        self.btn_incremental.setStyleSheet(
            self.style_resaltado if self.paso_actual == PASO_BACKUP else self.style_normal
        )
        
        # Cerrar siempre habilitado
        self.btn_cerrar.setEnabled(True)
        self.btn_cerrar.setStyleSheet(self.style_normal)

    def add_movil_adb(self):
        # Comprobar si ADB detecta un dispositivo
        try:
            salida = subprocess.check_output([ruta_adb(), "devices"], encoding="utf-8")

        except Exception:
            QMessageBox.warning(self, "Error ADB", "No se ha detectado un dispositivo con ADB.")
            return
        
        lineas = salida.strip().split("\n")

        # No hay dispositivos
        if len(lineas) <= 1:
            QMessageBox.warning(self, "Sin dispositivo", "No se ha detectado un dispositivo con ADB.")
            return
        
        # Buscar dispositivo en estado 'device'
        dispositivo = None
        for linea in lineas[1:]:
            if "device" in linea:
                dispositivo = linea.split()[0]
                break

        if not dispositivo:
            QMessageBox.warning(self, "Sin dispositivo", "No se ha detectado un dispositivo con ADB.")
            return
        
        # Añadir ruta virtual ADB como origen
        ruta_adb_movil = f"adb://{dispositivo}{ruta_movil()}"
        self.rutas_origen.append(ruta_adb_movil)
        self.lista_rutas.addItem(f"[ADB] {ruta_adb_movil}")

        self.log.append(f"Móvil detectado via ADB: {dispositivo}")

        self.paso_actual = PASO_CREAR_INDICE
        self.actualizar_botones()        

    def ajustar_ancho_por_log(self):
        texto = self.log.toPlainText()
        lineas = texto.split("\n")

        if not lineas:
            return
        
        # Longitud máxima en caracteres
        max_chars = max(len(linea) for linea in lineas)

        # Convertir caracteres a píxeles aproximados
        # Qt usa fuentes proporcionales, pero ~7 px por carácter es una 
        # buena aproximación.
        ancho_px = max_chars * 5

        # Añadir margen
        ancho_px += 100

        # Ajustar el ancho del diálogo
        self.resize(ancho_px, self.height())

        # Posicionar el formulario según el ancho del mismo.
        pantalla = QApplication.desktop().screenGeometry()
        nuevo_x = (pantalla.width() - self.width()) // 2
        nuevo_y = (pantalla.height() - self.height()) // 2
        self.move(nuevo_x, nuevo_y)
        
    def iniciar_progreso(self, total: int):
        self.progreso.setMinimum(0)
        self.progreso.setMaximum(total)
        self.progreso.setValue(0)

    def avanzar_progreso(self):
        self.progreso.setValue(self.progreso.value() + 1)
        QApplication.processEvents() # Evita bloqueo de UI

    def finalizar_progreso(self):
        self.progreso.setValue(self.progreso.maximum())
        
    def contar_archivos_pc(self, rutas_pc):
        total = 0
        for raiz in rutas_pc:
            for raiz, _, archivos in os.walk(raiz):
                total += len(archivos)

        return total
    
    def contar_archivos_adb(self, rutas_adb):
        total = 0
        for ruta in rutas_adb:
            total += len(self.adb_listar_archivos(ruta))

        return total
    
    def cargar_json_backup(self):
        ruta = os.path.join(get_ruta_backup(), "copia_seguridad", "archivos_unificados_backup.json")
        if not os.path.exists(ruta):
            QMessageBox.warning(self, "Backup", "No existe copia de seguridad.")
            return None
        
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    