'''
Script en Python.
'''

import unicodedata

from datetime import datetime
from collections import defaultdict

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QCheckBox, QComboBox, QProgressBar,
    QScrollArea, QWidget, QMessageBox
)
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QThread, Qt, pyqtSignal

from autodiagnostico.worker.worker_autodiagnostico import WorkerAutodiagnostico
from autodiagnostico.correcciones import CORRECCIONES
from autodiagnostico.servicios.json_service import cargar_json, guardar_json
from autodiagnostico.widgets import WidgetError

from config_manager import load_config, save_config
from config_paths import get_spinner

from utils.thread_manager import thread_manager

class DialogoAutodiagnostico(QDialog):
    cerrado = pyqtSignal() # Se emite cuando se cierra el diálogo

    def __init__(self, ruta_json, raiz_backup, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Autodiagnóstico del sistema")
        self.resize(600, 600)

        self._testing = False # Necesario para pruebas

        self.ruta_json = ruta_json
        self.raiz_backup = raiz_backup
        self.txtReporte = ""
        self.estado_chequeos = {} # Nombre -> QLabel

        layout = QVBoxLayout(self)

        # -------------------------
        # Selección de diagnósticos
        # -------------------------
        hseleccion = QHBoxLayout()
        hseleccion.setAlignment(Qt.AlignTop)

        hvchecks = QVBoxLayout()
        self.chkCompleto = QCheckBox("Diagnóstico completo")
        self.chkJsonCarpetas = QCheckBox("JSON ↔ Carpetas")
        self.chkJsonCache = QCheckBox("JSON ↔ Cache de ubicaciones")
        self.chkIntegridad = QCheckBox("Integridad de archivos")
        self.chkDirectorios = QCheckBox("Directorios vacíos")
        self.chkCorrupcion = QCheckBox("Archivos corruptos")

        # Jerarquía visual
        for chk in [
            self.chkJsonCarpetas, self.chkJsonCache, self.chkIntegridad,
            self.chkDirectorios, self.chkCorrupcion
        ]:
            chk.setStyleSheet("margin-left: 20px;")
        
        hvchecks.addWidget(self.chkCompleto)
        hvchecks.addWidget(self.chkJsonCarpetas)
        hvchecks.addWidget(self.chkJsonCache)
        hvchecks.addWidget(self.chkIntegridad)
        hvchecks.addWidget(self.chkDirectorios)
        hvchecks.addWidget(self.chkCorrupcion)

        self.chkCompleto.stateChanged.connect(self.toggle_completo)

        # -------------------------
        # Programación automática
        # -------------------------
        hprogramar = QVBoxLayout()
        hprogramar.setAlignment(Qt.AlignTop)
        hprogramar.addWidget(QLabel("Programar autodiagnóstico cada:"))

        hprog = QHBoxLayout()
        hprog.setContentsMargins(0, 0, 0, 0)
        hprog.setSpacing(5)

        self.chProgramar = QCheckBox("")
        self.chProgramar.stateChanged.connect(self.toggle_programar)
        
        self.cmbCantidad = QComboBox()
        self.cmbCantidad.addItems([str(i) for i in range(1, 11)])

        self.cmbUnidad = QComboBox()
        self.cmbUnidad.addItems(["días", "semanas", "meses"])

        hprog.addWidget(self.chProgramar)
        hprog.addWidget(self.cmbCantidad)
        hprog.addWidget(self.cmbUnidad)

        hprogramar.addLayout(hprog)

        hboton_prog = QVBoxLayout()
        hboton_prog.setContentsMargins(0, 0, 0, 0)
        hboton_prog.setSpacing(5)

        self.btnProgramar = QPushButton()
        self.btnProgramar.clicked.connect(self.programar_autodiagnostico)

        hboton_prog.addWidget(self.btnProgramar)

        hprogramar.addLayout(hboton_prog)

        hseleccion.addLayout(hvchecks)
        hseleccion.addLayout(hprogramar)

        layout.addLayout(hseleccion)

        self.comprobar_programar()

        # -------------------------
        # Spinner y etiqueta de estado
        # -------------------------
        hstatus = QHBoxLayout()

        hvestado = QVBoxLayout()
        self.lblEstado = QLabel("Pulsar (Empezar)")
        self.lblEstado.setAlignment(Qt.AlignCenter)

        self.lblSpinner = QLabel()
        self.movie = QMovie(get_spinner())
        self.lblSpinner.setMovie(self.movie)
        self.lblSpinner.setAlignment(Qt.AlignCenter)
        self.lblSpinner.hide()
        
        hvestado.addWidget(self.lblEstado)
        hvestado.addWidget(self.lblSpinner)        

        # -------------------------
        # Panel de progreso detallado
        # -------------------------
        hvprogreso = QVBoxLayout()
        self.lblProgresoTitulo = QLabel("Progreso del diagnóstico")
        self.lblProgresoTitulo.setStyleSheet("font-weight: bold; margin-top: 10px")

        self.panelProgreso = QWidget()
        self.layoutProgreso = QVBoxLayout(self.panelProgreso)
        self.layoutProgreso.setContentsMargins(10, 5, 10, 5)
        self.layoutProgreso.setSpacing(4)

        hvprogreso.addWidget(self.lblProgresoTitulo)
        hvprogreso.addWidget(self.panelProgreso)

        hstatus.addLayout(hvestado)
        hstatus.addLayout(hvprogreso)

        layout.addLayout(hstatus)

        # -------------------------
        # Barra de progreso
        # -------------------------
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # -------------------------
        # Zona de reporte
        # -------------------------
        self.scrolll = QScrollArea()
        self.scrolll.setWidgetResizable(True)

        self.contenedorReporte = QWidget()
        self.layoutReporte = QVBoxLayout(self.contenedorReporte)
        self.layoutReporte.setContentsMargins(10, 10, 10, 10)
        self.layoutReporte.setSpacing(15)

        self.scrolll.setWidget(self.contenedorReporte)
        layout.addWidget(self.scrolll)

        # -------------------------
        # Botones
        # -------------------------
        hbtn = QHBoxLayout()
        self.btnEmpezar = QPushButton("Empezar")
        self.btnCerrar = QPushButton("Cerrar")
        self.btnGuardar = QPushButton("Guardar reporte")
        self.btnGuardar.setEnabled(False)

        hbtn.addWidget(self.btnEmpezar)
        hbtn.addWidget(self.btnCerrar)
        hbtn.addWidget(self.btnGuardar)
        layout.addLayout(hbtn)

        # -------------------------
        # Conexiones
        # -------------------------
        self.btnEmpezar.clicked.connect(self.iniciar)
        self.btnCerrar.clicked.connect(self.close)
        self.btnGuardar.clicked.connect(self.guardar_reporte)

        self.thread_ = None
        self.worker = None

    def closeEvent(self, event):
        self.cerrado.emit()
        super().closeEvent(event)

    # ---------------------------------------------------------
    # Iniciar autodiagnóstico
    # ---------------------------------------------------------
    def iniciar(self):
        seleccionados = self.obtener_chequeos_seleccionados()
        if not seleccionados:
            QMessageBox.critical(self, "Error", "☣ Debes seleccionar al menos un diagnóstico.")
            return
        
        # Actualizar la fecha del último autodiagnóstico para comprobar
        #   la programación
        cfg = load_config()
        cfg["autodiagnostico_ultima"] = datetime.now().strftime("%Y-%m-%d")
        save_config(cfg)

        # Comprobar si se ha programado el autodiagnóstico
        self.progress.setMaximum(len(seleccionados) if "completo" not in seleccionados else 5)
        self.progress.setValue(0)

        self.inicializar_panel_progreso(seleccionados)

        self.lblSpinner.show()
        self.movie.start()

        # Crear hilo + worker
        self.thread_ = QThread()
        self.worker = WorkerAutodiagnostico(
            self.ruta_json,
            self.raiz_backup,
            seleccionados
        )
        self.worker.moveToThread(self.thread_)

        # Añadimos el hilo al gestor de hilos
        thread_manager.add(self.thread_)

        # Conexiones
        self.thread_.started.connect(self.worker.run)
        self.worker.progreso.connect(self.actualizar_estado)
        self.worker.avance.connect(self.actualizar_progreso)
        self.worker.estado_chequeo.connect(self.actualizar_progreso_detallado)
        self.worker.terminado.connect(self.mostrar_resultados)

        # Cuando termine, cerramos el hilo
        self.worker.terminado.connect(self.thread_.quit)
        self.worker.terminado.connect(self.worker.deleteLater)
        self.thread_.finished.connect(self.thread_.deleteLater)

        # Iniciar
        self.thread_.start()

    # ---------------------------------------------------------
    # Inicializar el panel de progreso detallado
    # ---------------------------------------------------------
    def inicializar_panel_progreso(self, chequeos):
        # Limpiar panel
        while self.layoutProgreso.count():
            item = self.layoutProgreso.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.estado_chequeos.clear()

        for chk in chequeos:
            lbl = QLabel(f"· {chk}")
            lbl.setStyleSheet("font-size: 13px;")
            self.layoutProgreso.addWidget(lbl)
            self.estado_chequeos[chk] = lbl

    # ---------------------------------------------------------
    # Obtener lista de chequeos seleccionados
    # ---------------------------------------------------------
    def toggle_completo(self, estado):
        checks = [
            self.chkJsonCarpetas,
            self.chkJsonCache, 
            self.chkIntegridad, 
            self.chkDirectorios, 
            self.chkCorrupcion
        ]

        if estado == Qt.Checked:
            for chk in checks:
                chk.setChecked(True)
                chk.setEnabled(False)
        else:
            for chk in checks:
                chk.setChecked(False)
                chk.setEnabled(True)

    def obtener_chequeos_seleccionados(self):
        if self.chkCompleto.isChecked():
            return [
                "json_carpetas",
                "json_cache",
                "integridad",
                "directorios",
                "corrupcion"
            ]
        
        lista = []
        if self.chkJsonCarpetas.isChecked(): lista.append("json_carpetas")
        if self.chkJsonCache.isChecked(): lista.append("json_cache")
        if self.chkIntegridad.isChecked(): lista.append("integridad")
        if self.chkDirectorios.isChecked(): lista.append("directorios")
        if self.chkCorrupcion.isChecked(): lista.append("corrupcion")
        return lista
    
    # ---------------------------------------------------------
    # Actualizar estado
    # ---------------------------------------------------------
    def actualizar_estado(self, mensaje):
        self.lblEstado.setText(mensaje)

    # ---------------------------------------------------------
    # Actualizar barra de progreso
    # ---------------------------------------------------------
    def actualizar_progreso(self):
        self.progress.setValue(self.progress.value() + 1)

    # ---------------------------------------------------------
    # Actualizar progreso detallado
    # ---------------------------------------------------------
    def actualizar_progreso_detallado(self, chk):
        # Marcar todos los anteriores como completados
        for nombre, lbl in self.estado_chequeos.items():
            if nombre == chk:
                lbl.setText(f"⌛ {nombre}")
                lbl.setStyleSheet("color: #0077cc; font-weight: bold;")
                break
            else:
                lbl.setText(f"✅ {nombre}")
                lbl.setStyleSheet("color: #009900; font-weight: bold;")

    # ---------------------------------------------------------
    # Programar autodiagnostico
    # ---------------------------------------------------------
    def programar_autodiagnostico(self):
        cfg = load_config()

        cantidad = int(self.cmbCantidad.currentText())
        unidad = self.cmbUnidad.currentText()
        self.btnProgramar.setText(f"Programar autodiagnóstico\ncada {cantidad} {unidad}")

        unidad_norm = unicodedata.normalize("NFKD", unidad)
        unidad_norm = "".join(c for c in unidad_norm if not unicodedata.combining(c))

        cfg["autodiagnostico_cantidad"] = cantidad
        cfg["autodiagnostico_unidad"] = unidad_norm
        cfg["autodiagnostico_ultima"] = datetime.now().strftime("%Y-%m-%d")

        save_config(cfg)
        
        self.mostrar_mensaje("Programación guardada con exito.")

    def toggle_programar(self, estado):
        activar = estado

        # Abrimos el config.
        cfg = load_config()

        self.chProgramar.setChecked(activar)
        self.cmbCantidad.setEnabled(activar)
        self.cmbUnidad.setEnabled(activar)

        # Definimos el texto del botón programar.
        if activar:
            cantidad = int(cfg["autodiagnostico_cantidad"])
            unidad = cfg["autodiagnostico_unidad"]
            self.btnProgramar.setText(f"Programar autodiagnóstico\ncada {cantidad} {unidad}")
        else:
            self.btnProgramar.setText("Programar autodiagnóstico")

        self.btnProgramar.setEnabled(activar)

        # Guardar en config
        cfg["autodiagnostico_activar"] = "True" if activar else "False"
        save_config(cfg)

    def comprobar_programar(self):
        cfg = load_config()
        programar_ok = cfg["autodiagnostico_activar"] == "True"
        self.toggle_programar(programar_ok)

    # ---------------------------------------------------------
    # Mostrar resultados
    # ---------------------------------------------------------
    def mostrar_resultados(self, reporte):
        self.movie.stop()
        self.lblSpinner.hide()

        # Limpiar reporte anterior
        while self.layoutReporte.count():
            item = self.layoutReporte.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Agrupar problemas
        grupos = defaultdict(list)
        for bloque in reporte:
            nombre_bloque = bloque["nombre"]
            for p in bloque["problemas"]:
                tipo = p.get("tipo", "desconocido")
                grupos[(nombre_bloque, tipo)].append(p)

        self.txtReporte = ""

        for (nombre_bloque, tipo), lista_problemas in grupos.items():
                # Título del grupo
                titulo = f"🔎 {nombre_bloque} - {tipo.replace('_', ' ').title()} ({len(lista_problemas)})"

                # Construir detalle
                detalle = ""
                for p in lista_problemas:
                    detalle += f" · {p.get('detalle')}\n"

                # Crear widget
                widget = WidgetError(
                    titulo=titulo,
                    detalle = detalle,
                    callback_corregir=lambda _, lista=lista_problemas: self.corregir_grupo(lista)
                )

                self.txtReporte += f"{titulo}\n{detalle}\n\n"
                self.layoutReporte.addWidget(widget)

        # Habilitar botón
        self.btnGuardar.setEnabled(True)

        # Marcos todos como completados
        for nombre, lbl in self.estado_chequeos.items():
            lbl.setText(f"✅ {nombre}")
            lbl.setStyleSheet("color: #009900; font-weight: bold;")

    # ---------------------------------------------------------
    # Corrección modular
    # ---------------------------------------------------------
    def corregir_grupo(self, lista_problemas):
        tipo = lista_problemas[0].get("tipo")

        data = cargar_json(self.ruta_json)
        data = CORRECCIONES[tipo](lista_problemas, data)
        guardar_json(self.ruta_json, data)

        self.mostrar_mensaje("La corrección ha sido realizada correctamente.")

        # Re-ejecutar diagnóstico
        self.iniciar()

    # ---------------------------------------------------------
    # Guardar reporte
    # ---------------------------------------------------------
    def guardar_reporte(self):
        date = datetime.now().strftime("%d/%m/%Y - %H:%M")
        with open("reporte_autodiagnostico.txt", "w", encoding="utf-8") as f:
            f.write(date + '\n\n')
            f.write(self.txtReporte)
            
        self.mostrar_mensaje("💾 Reporte guardado en 'reporte_autodiagnostico.txt'")

    def mostrar_mensaje(self, mensaje):
        if getattr(self, "_testing", False):
            return
        QMessageBox.information(self, "Información", mensaje)
