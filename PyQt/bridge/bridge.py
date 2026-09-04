'''

'''

import os, re
import json
import shutil
import config_manager

from pathlib import Path
from PyQt5.QtWidgets import (
    QHBoxLayout, QWidget, QMessageBox, QFileDialog, QDialog,
    QVBoxLayout, QCheckBox, QLabel
)
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt5.QtGui import QPixmap, QColor, QTransform
from PyQt5.QtCore import Qt
from PIL import Image

from componentes.controles import (
    Button, CheckBox, SpinnerOverlay, SelectorCarpeta, HeaderWidget
    )
from copia_clasificador_fotos import (
    cargar_json_unico, guardar_json_unico, actualizar_stats, calcular_hash_md5
    )
from mapa_generator import extraer_ciudad
from config_paths import (
    ruta_json_unico, meses, get_ruta_mapa_fotos_html, extensiones_validas,
    get_ruta_miniaturas
    )
from utils.utils_cache import cargar_cache
from utils.thread_manager import thread_manager
from worker.mapa_worker import MapaWorker
from worker.copia_worker import CopiaWorker
from componentes.progreso_dialog import ProgresoClasificacion
from componentes.custom_mensage_box import CustomMessageBox
from compartir.main import VentanaPrincipal as VentanaCompartir


ARCHIVOS_SEL = {}  # clave: ruta_archivo, valor: hash_archivo

class WidgetGaleria(QWidget):
    seleccionado = pyqtSignal(object, bool) # (widget, estado)

    def __init__(self, ruta, hash_archivo, miniatura, tamano, ruta_thumb=None, parent=None):
        super().__init__(parent)

        self.ruta = ruta
        self.hash = hash_archivo
        self.miniatura = miniatura
        self.nombre = os.path.basename(ruta)

        layout = QVBoxLayout(self) if miniatura else QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)

        # === Checkbox ===
        self.chk = QCheckBox()
        self.chk.stateChanged.connect(self._emitir_cambio)
        layout.addWidget(self.chk, alignment=Qt.AlignRight)

        # === Miniatura ===
        if miniatura:
            lbl_thumb = QLabel()
            lbl_thumb.setAlignment(Qt.AlignCenter)

            img = Image.open(ruta_thumb if ruta_thumb else ruta)
            exif = img.getexif()
            orientacion = exif.get(274, 1)

            pix = QPixmap(ruta_thumb if ruta_thumb else ruta).scaled(
                tamano, tamano, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            transform = QTransform()
            if orientacion == 3:
                transform.rotate(180)
            elif orientacion == 6:
                transform.rotate(90)
            elif orientacion == 8:
                transform.rotate(270)
            pix = pix.transformed(transform)
            
            lbl_thumb.setPixmap(pix)
            lbl_thumb.setAlignment(Qt.AlignCenter)

            layout.addWidget(lbl_thumb)

        # === Nombre ===
        lbl_nombre = QLabel(self.nombre)
        lbl_nombre.setAlignment(Qt.AlignCenter)
        lbl_nombre.setStyleSheet("font-size: 9px; color: #444;")
        layout.addWidget(lbl_nombre)

    def _emitir_cambio(self, state):
        self.seleccionado.emit(self, state == Qt.Checked)

    def setSeleccionado(self, estado):
        self.chk.setChecked(estado)

    def isSeleccionado(self):
        return self.chk.isChecked()

    @property
    def filepath(self):
        return getattr(self, "ruta", None)
        
class Bridge(QObject):
    actualizarFoto = pyqtSignal(str)
    pendientes_actualizados = pyqtSignal(int)
    enviarListaArchivos = pyqtSignal(str)

    def __init__(self, tableWidget, tableClasificacion, labelFechaListado, labelArchivosSeleccionadosClasificacion,
                 labelMapaActualizado, button_generar_mapa, button_sel_multiple, view, labelFoto, ruta_json,
                 set_mapa_habilitado_callback, contar_pendientes):
        super().__init__()
        self.tabla = tableWidget
        self.tablaClasificacion = tableClasificacion
        self.label = labelFechaListado
        self.labelArcSelCla = labelArchivosSeleccionadosClasificacion
        self.numArcSel = 0 # Número de Archivos Seleccionados
        self.labelStatus = labelMapaActualizado
        self.boton_generar_mapa = button_generar_mapa
        self.boton = button_sel_multiple
        self.view = view
        self.labelFoto = labelFoto
        self.ruta_json = ruta_json
        self.actual_ruta = None
        self.set_mapa_habilitado = set_mapa_habilitado_callback
        self.contar_pendientes = contar_pendientes

        # Definir vista de la aplicación 'Principal', 'Clasificación'
        self.vista_actual = 0

    # ============================================================
    # RECEPCIÓN DE RUTA DESDE JS
    # ============================================================
    @pyqtSlot(str)
    def recibirRuta(self, ruta):
        # Normalizar ruta para las barras invertidas (\\)
        self.actual_ruta = os.path.normpath(ruta)
        self.enviarListaArchivos.emit(self.actual_ruta)
        self.actualizar_tabla()
        # Cargamos la galería de clasificación si esta en esa vista.
        if self.vista_actual == 1: self.cargar_galeria(self.actual_ruta, True)

    @pyqtSlot('QVariantMap')
    def recibirListaArchivos(self, datos):
        lista_rutas = datos.get("rutas", [])
        titulo = datos.get("titulo", "Grupo")

        self.lista_archivos = [os.path.normpath(r) for r in lista_rutas]
        self.actual_ruta = None

        # Mostrar el nombre del grupo
        self.label.setText(titulo)

        # Mostrar tabla con todos los archivos seguidos
        self.actualizar_tabla_desde_lista()

        # Si estás en la vista de clasificación -> mostrar galería unificada
        if self.vista_actual == 1:
            self.cargar_galeria_desde_lista(self.lista_archivos, True)

    def set_vista(self, indice):
        self.vista_actual = indice

    # ============================================================
    # TABLA
    # ============================================================
    def actualizar_tabla_desde_lista(self):
        ARCHIVOS_SEL.clear()

        self.data = cargar_json_unico(ruta_json_unico())
        self.historial = self.data["clasificados"]["items"]
        self.eliminado = self.data["eliminados"]["items"]
        self.pendientes = self.data["pendientes"]["items"]

        archivos = self.lista_archivos
        self.numero_archivos = len(archivos)

        self.tabla.setVisible(True)
        self.tabla.setRowCount(self.numero_archivos)
        self.tabla.setColumnCount(5)

        self.tabla.setStyleSheet("""
            QTableWidget::item {
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QTableWidget::item:selected {
                color: black;
                background-color: lightblue;
            }
        """)

        self.tabla.setHorizontalHeaderLabels(
            ['Sel', 'Nombre de Archivo', 'Ruta', 'Acción', 'Hash']
        )

        tamaño = 185 if self.numero_archivos > 8 else 205
        self.tabla.setColumnWidth(0, 40)
        self.tabla.setColumnWidth(1, tamaño)
        self.tabla.setColumnWidth(3, 140)

        self.tabla.setColumnHidden(0, True)
        self.tabla.setColumnHidden(2, True)
        self.tabla.setColumnHidden(4, True)

        self.tabla.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tabla.horizontalHeader().setSectionsClickable(False)

        for i, ruta_completa in enumerate(archivos):
            nombre = os.path.basename(ruta_completa)
            ruta_conver = os.path.normpath(ruta_completa)

            busqueda_hash = (
                self.pendientes if '(Sin_GPS)' in ruta_conver else self.historial
            )

            coincidencia = next(
                (r for r in busqueda_hash if os.path.normpath(r['ruta']) == ruta_conver),
                None
            )

            hash_val = coincidencia['hash'] if coincidencia else ""
            fecha_val = coincidencia.get('fecha', "") if coincidencia else ""

            # Nombre del archivo con el tooltip de la fecha.
            item_nombre = QTableWidgetItem(nombre)
            if fecha_val:
                item_nombre.setToolTip(fecha_val)

            self.tabla.setCellWidget(i, 0, self.boton_checkbox(i))
            self.tabla.setItem(i, 1, item_nombre)
            self.tabla.setItem(i, 2, QTableWidgetItem(ruta_completa))
            self.tabla.setCellWidget(i, 3, self.botones_accion(i))
            self.tabla.setItem(i, 4, QTableWidgetItem(hash_val))
            self.tabla.setRowHeight(i, 30)

        if self.tabla.rowCount() > 0:
            self.tabla.setCurrentCell(0, 1)
            ruta_archivo = self.tabla.item(0, 2).text()
            self.actualizarFoto.emit(ruta_archivo)

    def actualizar_tabla(self):
        ARCHIVOS_SEL.clear()

        self.data = cargar_json_unico(ruta_json_unico())
        self.historial = self.data["clasificados"]["items"]
        self.eliminado = self.data["eliminados"]["items"]
        self.pendientes = self.data["pendientes"]["items"]

        if not self.actual_ruta:
            return

        if not os.path.isdir(self.actual_ruta):
            QMessageBox.warning(None, "Error", f"No se encontró el directorio:\n{self.actual_ruta}")
            return

        archivos = os.listdir(self.actual_ruta)
        self.numero_archivos = len(archivos)

        self.tabla.setVisible(True)
        self.tabla.setRowCount(self.numero_archivos)
        self.tabla.setColumnCount(5)

        self.tabla.setStyleSheet("""
            QTableWidget::item {
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QTableWidget::item:selected {
                color: black;
                background-color: lightblue;
            }
        """)

        self.tabla.setHorizontalHeaderLabels(
            ['Sel', 'Nombre de Archivo', 'Ruta', 'Acción', 'Hash']
        )

        tamaño = 185 if self.numero_archivos > 8 else 205
        self.tabla.setColumnWidth(0, 40)
        self.tabla.setColumnWidth(1, tamaño)
        self.tabla.setColumnWidth(3, 140)

        self.tabla.setColumnHidden(0, True)
        self.tabla.setColumnHidden(2, True)
        self.tabla.setColumnHidden(4, True)

        self.tabla.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.tabla.horizontalHeader().setSectionsClickable(False)

        mes, ano, lugar = self.obtener_fecha_lugar(self.actual_ruta)
        texto = 'Pendientes' if ano == '0000' else f'{lugar}\n{mes} de {ano}'
        self.label.setText(texto)

        for i, nombre in enumerate(archivos):
            ruta_completa = os.path.join(self.actual_ruta, nombre)
            ruta_conver = os.path.normpath(ruta_completa)

            busqueda_hash = (
                self.pendientes if '(Sin_GPS)' in ruta_conver else self.historial
            )

            coincidencia = next(
                (r for r in busqueda_hash if os.path.normpath(r['ruta']) == ruta_conver),
                None
            )

            hash_val = coincidencia['hash'] if coincidencia else ""
            fecha_val = coincidencia.get('fecha', "") if coincidencia else ""

            # Nombre del archivo con el tooltip de la fecha.
            item_nombre = QTableWidgetItem(nombre)
            if fecha_val:
                item_nombre.setToolTip(fecha_val)

            self.tabla.setCellWidget(i, 0, self.boton_checkbox(i))
            self.tabla.setItem(i, 1, item_nombre)
            self.tabla.setItem(i, 2, QTableWidgetItem(ruta_completa))
            self.tabla.setCellWidget(i, 3, self.botones_accion(i))
            self.tabla.setItem(i, 4, QTableWidgetItem(hash_val))
            self.tabla.setRowHeight(i, 30)

        if self.tabla.rowCount() > 0:
            self.tabla.setCurrentCell(0, 1)
            ruta_archivo = self.tabla.item(0, 2).text()
            self.actualizarFoto.emit(ruta_archivo)

    # ============================================================
    # CHECKBOXES
    # ============================================================
    def boton_checkbox(self, row):
        check = QWidget()
        sel_check = CheckBox()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        sel_check.stateChanged.connect(lambda state, r=row: self.state_change_ckeckbox(r, state))
        layout.addWidget(sel_check)
        layout.setAlignment(Qt.AlignCenter)
        check.setLayout(layout)
        return check

    def botones_accion(self, row, col=None):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        copiar_button = Button('copy', '#B2B3AD')
        copiar_button.setToolTip("Copiar")
        mover_button = Button('move', '#AEB626')
        mover_button.setToolTip("Mover")
        compartir_button = Button('share', '#0BAFBA')
        compartir_button.setToolTip("Compartir")
        borrar_button = Button('delete', '#f08080')
        borrar_button.setToolTip("Borrar")

        copiar_button.clicked.connect(lambda _, r=row, c=col: self.accion("copiar", r, c))
        mover_button.clicked.connect(lambda _, r=row, c=col: self.accion("mover", r, c))
        compartir_button.clicked.connect(lambda _, r=row, c=col: self.accion("compartir", r, c))
        borrar_button.clicked.connect(lambda _, r=row, c=col: self.accion("borrar", r, c))

        layout.addWidget(copiar_button)
        layout.addWidget(mover_button)
        layout.addWidget(compartir_button)
        layout.addWidget(borrar_button)

        widget.setLayout(layout)
        return widget
    
    def accion(self, accion, row=None, col=None):
        # Determinar tabla y selección
        if self.vista_actual == 0 and row is not None and row >=0:
            tabla = self.tabla
            selecciones = [] # En vista lista usas row/col directo
        elif self.vista_actual == 1:
            tabla, selecciones = self.obtener_seleccion()
        else:
            return

        if tabla is None:
            QMessageBox.warning(None, "Sin selección", "No hay ningún archivo seleccionado.")
            return
        
        # Diccionario de acciones disponibles
        acciones = {
            "copiar": self.copiar,
            "mover": self.mover,
            "compartir": self.compartir,
            "borrar": self.borrar
        }

        # Obtener la función correspondiente
        funcion = acciones.get(accion)
        if funcion is None:
            print(f"Acción desconocida: {accion}")
            return
        
        # Si hay selección múltiple, ARCHIVOS_SEL ya está lleno
        if ARCHIVOS_SEL:
            funcion()
            return
        
        # Si no hay selección global, usar las selecciones encontradas
        if selecciones:
            # Rellenar ARCHIVOS_SEL con las ruta encontradas
            for _, _, filepath in selecciones:
                if filepath:
                    # Calcular hash si lo necesitas
                    hash_archivo = calcular_hash_md5(filepath)
                    ARCHIVOS_SEL[filepath] = hash_archivo

            funcion()
            return
        
        # Si no hay selección en galeria, usar row/col (vista lista)
        funcion(row, col)

    def obtener_fecha_lugar(self, dato):
        fecha = dato.split(')')[2][1:]
        lugar = dato.split('(')[1].split(')')[0]
        ano = fecha[0:4]
        mes = meses()[int(fecha[5:]) - 1]
        return mes, ano, lugar

    def state_change_ckeckbox(self, row, state_int, col=None):
        ruta_archivo, hash_archivo = self.obtener_archivo(row, col)
        state = Qt.CheckState(state_int)

        if state == Qt.Checked:
            ARCHIVOS_SEL[ruta_archivo] = hash_archivo
        else:
            ARCHIVOS_SEL.pop(ruta_archivo, None)

    # ============================================================
    # CLASIFICACIÓN CON PROGRESO
    # ============================================================
    def iniciar_clasificacion(self, ruta, modo, inicio, fin):
        """Lanza el worker de clasificación con barra de progreso."""
        self.worker_copia = CopiaWorker(ruta, modo, inicio, fin)

        # Registrar hilo en el gestor.
        thread_manager.add(self.worker_copia)

        self.worker_copia.total.connect(self._crear_dialogo_progreso)
        self.worker_copia.progreso.connect(self._actualizar_dialogo_progreso)
        self.worker_copia.terminado.connect(self._cerrar_dialogo_progreso)
        #self.worker_copia.terminado.connect(self._clasificacion_finalizada)

        self.worker_copia.start()

    def _crear_dialogo_progreso(self, total):
        self.dialogo_progreso = ProgresoClasificacion(total)
        self.dialogo_progreso.cancelar.connect(self._cancelar_clasificacion)
        self.dialogo_progreso.show()

    def _actualizar_dialogo_progreso(self, tipo_resultado):
        if hasattr(self, "dialogo_progreso"):
            self.dialogo_progreso.actualizar(tipo_resultado)

    def _cerrar_dialogo_progreso(self, mensaje):
        if hasattr(self, "dialogo_progreso"):
            msg = QMessageBox.information(
                None, "Clasificación finalizada",
                  "Desea ver la información?",
                  QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
            )
            if msg == QMessageBox.Yes:
                dlg = CustomMessageBox("Clasificación finalizada", mensaje, None)
                dlg.exec_()

            self.dialogo_progreso.close()
            self._clasificacion_finalizada(None)

    def _clasificacion_finalizada(self, _):
        self.cargar_pendientes()

        self.spinner = SpinnerOverlay(self.view, "Generando el mapa...")
        self.spinner.show()

        self.worker_clasificacion = MapaWorker()

        # Registrar el hilo en el gestor.
        thread_manager.add(self.worker_clasificacion)

        self.worker_clasificacion.pendientes_actualizados.connect(self._reenviar_pendientes)
        self.worker_clasificacion.terminado.connect(self.mapa_generado)
        self.worker_clasificacion.start()

    def _cancelar_clasificacion(self):
        if hasattr(self, "worker_copia"):
            self.worker_copia.stop_thread()
        self.dialogo_progreso.close()

    # ============================================================
    # COPIAR / MOVER / BORRAR (SIN CAMBIOS)
    # ============================================================

    def copiar(self, row=None, col=None):
        # Selección de la carpeta de destino. Abre el selector de carpetas.
        # El argumento 'None' es porque no hereda de un QWidget, ya que hereda
        #   de 'Bridge'.
        carpeta_destino = QFileDialog.getExistingDirectory(None, "Seleccionar carpeta de destino")
        if not carpeta_destino:
            return # El usuario canceló.
        
        # Obtenemos la lista de los archivos o el archivo a copiar.
        if not ARCHIVOS_SEL:
            ruta_archivo, hash_archivo = self.obtener_archivo(row, col)
            ARCHIVOS_SEL[ruta_archivo] = hash_archivo

        # Extraemos el nombre del archivo con 'basename' para evitar
        #   duplicar rutas.
        errores = []
        for archivo, _ in ARCHIVOS_SEL.items():
            nombre = os.path.basename(archivo)
            destino = os.path.join(carpeta_destino, nombre)
            try:
                shutil.copy2(archivo, destino)
                print(f'Copiado: {archivo} ➡ {destino}')
            except Exception as e:
                errores.append((archivo, str(e)))
                print(f'Error al copiar {archivo}: {e}')

        # Mensaje final
        if errores:
            mensaje = "Algunos archivos no se pudieron copiar: \n\n"
            mensaje += "\n".join(f"{a}: {err}" for a, err in errores)
            QMessageBox.warning(None, "Errores al copiar", mensaje)
        else:
            QMessageBox.information(None, "Copia completada", "Todos los archivos copiados\ncorrectamente.")

    def mover(self, row=None, col=None):
        carpeta_destino = ''
        dlg = SelectorCarpeta(self.actual_ruta, None)

        if dlg.exec_() == QDialog.Accepted:
            carpeta_destino = dlg.carpeta_seleccionada()
        
        if not carpeta_destino:
            return # El usuario canceló.
        
        # Cargar JSON unificado
        self.data = cargar_json_unico(ruta_json_unico())
        self.historial = self.data["clasificados"]["items"]
        self.pendientes = self.data["pendientes"]["items"]

        # Obtenemos la lista de los archivos o el archivo a mover.
        if not ARCHIVOS_SEL:            
            ruta_archivo, hash_archivo = self.obtener_archivo(row, col)
            ARCHIVOS_SEL[ruta_archivo] = hash_archivo

        # Extraemos el nombre del archivo con 'basename' para evitar
        #   duplicar rutas.
        errores = []
        for archivo, hash in ARCHIVOS_SEL.items():
            nombre = os.path.basename(archivo)
            origen = os.path.dirname(os.path.abspath(archivo))
            destino = os.path.join(carpeta_destino, nombre)
            try:
                shutil.copy2(archivo, destino)
                os.remove(archivo)

                # Normalizar ruta para JSON
                destino_norm = destino.replace('/', '//')

                # Buscar en clasificados
                entrada = next((e for e in self.historial if e["hash"] == hash), None)

                # Si no está en clasificados, buscar en pendientes
                if entrada is None:
                    entrada = next((e for e in self.pendientes if e["hash"] == hash), None)
                
                if entrada is None:
                    print(f'No se encontró el hash {hash} en el JSON.')

                # Actualizar ruta.
                entrada["ruta"] = destino_norm

                # Extraer ciudad, país, fecha desde la ruta
                parentesis = re.findall(r'\([^)]+\)', destino_norm)
                resultado = ''.join(parentesis)
                ciudad, pais, fecha = extraer_ciudad(resultado)

                ubicacion = f"({ciudad})({pais})"
                entrada["ubicacion"] = ubicacion
                entrada["fecha"] = f"({fecha})"

                # Extraer coordenadas desde cache.
                cache_geocoding = cargar_cache()
                clave_norm = ubicacion
                if clave_norm in cache_geocoding:
                    entrada["latitud"] = cache_geocoding[clave_norm]["lat"]
                    entrada["longitud"] = cache_geocoding[clave_norm]["lon"]
                
                # --- LOGICA DE CLASIFICACIÓN AUTOMÁTICA ---
                if ciudad == 'Sin_GPS':
                    # Mover a pendientes.
                    if entrada in self.historial:
                        self.historial.remove(entrada)
                    if entrada not in self.pendientes:
                        self.pendientes.append(entrada)
                else:
                    # Mover a clasificados.
                    if entrada in self.pendientes:
                        self.pendientes.remove(entrada)
                    if entrada not in self.historial:
                        self.historial.append(entrada)

            except Exception as e:
                errores.append((archivo, str(e)))
                print(f'Error al mover {archivo}: {e}')

        # Actualizar estadísticas.
        actualizar_stats(self.data)

        # Guardar JSON unificado
        guardar_json_unico(ruta_json_unico(), self.data)

        # Emitir actualización de pendientes.
        self.actualizar_contador_pendientes()

        if self.directorio_vacio(origen):
            self.limpiar_tabla(origen)

        # Mensaje final
        if errores:
            mensaje = "Algunos archivos no se pudiero mover: \n\n"
            mensaje += "\n".join(f"{a}: {err}" for a, err in errores)
            QMessageBox.warning(None, "Errores al mover", mensaje)
        else:
            QMessageBox.information(None, "Acción completada", "Todos los archivos fueron\nmovidos correctamente.")

        respuesta = self.pregunta_generar_mapa()

        if respuesta == QMessageBox.No:
            # Deshabilitar mapa y opciones relacionadas
            self.set_mapa_habilitado(False)

            config_manager.settings.setValue("Estado/mapa_generado", "False")
            config_manager.settings.sync()            

            self.actualizar_tabla()
            self.cargar_galeria(self.actual_ruta, True)
            return

        # Generar el mapa
        self.set_mapa_habilitado(True)

        self.spinner = SpinnerOverlay(self.view, "Generando el mapa...")
        self.spinner.show()

        self.worker_mover = MapaWorker()

        # Registrar el hilo en el gestor.
        thread_manager.add(self.worker_mover)
        
        self.worker_mover.pendientes_actualizados.connect(self._reenviar_pendientes)
        self.worker_mover.terminado.connect(self.mapa_generado)
        self.worker_mover.start()

        self.actualizar_tabla()
        self.cargar_galeria(self.actual_ruta, True)

    def compartir(self, row=None, col=None):
        if not ARCHIVOS_SEL:
            ruta_archivo, hash_archivo = self.obtener_archivo(row, col)
            ARCHIVOS_SEL[ruta_archivo] = hash_archivo

        self.dlg_compartir = VentanaCompartir(ARCHIVOS_SEL.keys())
        self.dlg_compartir.exec_()

    def borrar(self, row=None, col=None):
        mensaje = 'Archivo(s):\n'

        # Cargar JSON unificado.
        self.data = cargar_json_unico(ruta_json_unico())
        self.historial = self.data["clasificados"]["items"]
        self.pendientes = self.data["pendientes"]["items"]
        self.eliminado = self.data["eliminados"]["items"]

        # Obtenemos la lista de los archivos o el archivo a borrar.
        if not ARCHIVOS_SEL:
            ruta_archivo, hash_archivo = self.obtener_archivo(row, col)
            ARCHIVOS_SEL[ruta_archivo] = hash_archivo

        # Construir mensaje de confirmación.
        for archivo, _ in ARCHIVOS_SEL.items():
            nombre = os.path.basename(archivo)
            mensaje += f"- ({nombre}) ❌ Eliminar?.\n"

        origen = self.origen_de_seleccion(row)

        res = QMessageBox.question(None, f"Borrado de {origen}.", 
                                   mensaje,
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if res != QMessageBox.Yes:
            QMessageBox.information(None, "Borrado de archivos", "Borrado cancelado por el usuario.")
            return
        
        # Procesar borrado
        for archivo, hash in ARCHIVOS_SEL.items():
            try:
                os.remove(archivo) # Borramos el archivo físico.

                # Añadir a eliminados si no estaba ya.
                if not any(e["hash"] == hash for e in self.eliminado):
                    self.eliminado.append({"hash": hash})

                # Eliminar de clasificados.
                self.historial[:] = [e for e in self.historial if e["hash"] != hash]

                # Eliminar de pendientes.
                self.pendientes[:] = [e for e in self.pendientes if e["hash"] != hash]

            except Exception as e:
                print(f'Error al borrar {archivo}: {e}')

        QMessageBox.information(None, "Borrado de archivos", "Borrado Completado con éxito.")

        # Actualizar estadístitcas.
        self.data["stats"]["total_clasificados"] = len(self.historial)
        self.data["stats"]["total_pendientes"] = len(self.pendientes)
        self.data["stats"]["total_eliminados"] = len(self.eliminado)

        # Guardar JSON unificado.
        guardar_json_unico(ruta_json_unico(), self.data)

        # Emitir actualización de pendientes.
        self.actualizar_contador_pendientes()

        # Comprobamos si existe el directorio para actualizar la
        #   tabla o no.
        if self.directorio_vacio(origen):
            self.limpiar_tabla(origen)            

        respuesta = self.pregunta_generar_mapa()

        if respuesta == QMessageBox.No:
            # Deshabilitar mapa y opciones relacionadas
            self.set_mapa_habilitado(False)

            config_manager.settings.setValue("Estado/mapa_generado", "False")
            config_manager.settings.sync()

            self.actualizar_tabla()
            self.cargar_galeria(self.actual_ruta, True)
            return

        # Generar el mapa
        self.set_mapa_habilitado(True)            

        self.spinner = SpinnerOverlay(self.view, "Generando el mapa...")
        self.spinner.show()

        self.worker_borrar = MapaWorker()

        # Registrar el hilo en el gestor.
        thread_manager.add(self.worker_borrar)
        
        self.worker_borrar.pendientes_actualizados.connect(self._reenviar_pendientes)
        self.worker_borrar.terminado.connect(self.mapa_generado)
        self.worker_borrar.start()

        self.actualizar_tabla()
        self.cargar_galeria(self.actual_ruta, True)

    def obtener_seleccion(self):
        tabla = self.tablaClasificacion
        seleccion = [] # Lista de tuplas (row, col, filepath)

        # == VISTA CLASIFICACIÓN (galería) ===
        for row in range(tabla.rowCount()):
            # Si la fila es header, saltarla
            item0 = tabla.item(row, 0)
            if item0 and item0.data(Qt.UserRole) == "header":
                continue

            for col in range(tabla.columnCount()):
                widget = tabla.cellWidget(row, col)
                if not widget:
                    continue

                # Comprobaciones seguras para distintos nombres de checkbox
                checked = False
                # 1 método expuesto por WidgetGaleria
                if hasattr(widget, "isSeleccionado") and callable(widget.isSeleccionado):
                    try:
                        checked = widget.isSeleccionado()
                    except Exception:
                        checked = False
                # 2 método público setSeleccionado / atributo checkbox
                elif hasattr(widget, "chk") and hasattr(widget.chk, "isChecked"):
                    checked = widget.chk.isChecked()
                elif hasattr(widget, "checkbox") and hasattr(widget.checkbox, "isChecked"):
                    checked = widget.checkbox.isChecked()
                # 3 si el widget tiene setSeleccionado, quizá también tenga atributo interno
                elif hasattr(widget, "isChecked") and callable(widget.isChecked):
                    try:
                        checked = widget.isChecked()
                    except Exception:
                        checked = False

                if checked:
                    filepath = getattr(widget, "ruta", None) or getattr(widget, "filepath", None)
                    seleccion.append((row, col, filepath))

        # Devolver la tabla y la lista de selecciones (vacía si no hay)
        if seleccion:
            return tabla, seleccion
        return None, []

    def limpiar_tabla(self, origen):
        os.rmdir(origen)
        self.tabla.clearContents()
        self.tabla.setVisible(False)
        self.labelFoto.setPixmap(QPixmap())
        self.actual_ruta = None

    def origen_de_seleccion(self, row, col=None):
        '''
        Devuelve la carpeta origen a partir de:
        - la colección global ARCHIVOS_SEL si ya tiene elementos
        - o del archivo obtenido con obtener_archivo(row) si está vacía.
        '''
        if ARCHIVOS_SEL:
            # Tomar la carpeta del primer archivo en la selcción
            primer_archivo = next(iter(ARCHIVOS_SEL.keys()))
            return os.path.dirname(os.path.abspath(primer_archivo))
        else:
            ruta_archivo, _ = self.obtener_archivo(row, col)
            return os.path.dirname(os.path.abspath(ruta_archivo))
        
    # ============================================================
    # VISTA CLASIFICACIÓN
    # ============================================================
    def cargar_galeria_desde_lista(self, lista_rutas, miniatura, tamano=100):
        try:
            ARCHIVOS_SEL.clear()
            self.numArcSel = 0
            self.labelArcSelCla.setText(f'{self.numArcSel} archivo/s seleccionados.')

            #archivos = os.listdir(ruta)
            NUM_COLS = 7 if tamano == 180 else 13

            # 1️⃣ Agrupar archivos por fecha completa
            from collections import defaultdict
            grupos = defaultdict(list)

            for ruta_completa in lista_rutas:
                #ruta_completa = os.path.join(ruta, archivo)

                # Obtener fecha completa para agrupar
                fecha_completa = self.obtener_fecha_json(ruta_completa, self.data)
                grupos[fecha_completa].append(ruta_completa)

            # Ordenar por fecha
            grupos = dict(sorted(grupos.items()))

            # 2️⃣ Preparar la tabla
            self.tablaClasificacion.clearContents()
            self.tablaClasificacion.setColumnCount(NUM_COLS)

            # Mapa fecha > fila del header (para búsqueda rápida)
            self._fila_por_fecha = {}

            fila_actual = 0

            # 3️⃣ Dibujar encabezados + miniaturas
            for fecha, archivos_dia in grupos.items():

                # ---- Encabezado de fecha ----
                self.tablaClasificacion.insertRow(fila_actual)

                # Si la ruta contiene 'Sin_GPS' -> dibujar encabezado
                #if 'Sin_GPS' in ruta:

                # Widget con checkbox + fecha
                header_widget = HeaderWidget(fecha)
                header_widget.toggled.connect(self._seleccionar_grupo)

                # Expandir encabezado a todas las columnas
                self.tablaClasificacion.setCellWidget(fila_actual, 0, header_widget)
                self.tablaClasificacion.setSpan(fila_actual, 0, 1, NUM_COLS)

                # Marcar TODA la fila como header
                for col in range(NUM_COLS):
                    item_header = QTableWidgetItem()                
                    item_header.setData(Qt.UserRole, "header") # Para saber que fila es encabezado
                    # Evitar selección de la fila header
                    item_header.setFlags(Qt.ItemIsEnabled)
                    self.tablaClasificacion.setItem(fila_actual, col, item_header)

                # Guardar fila del header
                self._fila_por_fecha[fecha] = fila_actual

                fila_actual += 1 # Avenzar después del encabezado
                col = 0

                # ---- Miniaturas del día ----
                for ruta_completa in archivos_dia:

                    if col == 0:
                        self.tablaClasificacion.insertRow(fila_actual)

                    #ruta_completa = os.path.join(ruta, archivo)

                    # Obtener hash
                    hash_archivo = calcular_hash_md5(ruta_completa)

                    # Miniatura si es video
                    ruta_thumb = None
                    nombre_archivo = os.path.basename(ruta_completa)
                    if nombre_archivo.lower().endswith(extensiones_validas("video")):
                        ruta_thumb = self.obtener_ruta_miniatura(hash_archivo)
                        # Usar miniatura
                        mini = Path(__file__).parent.parent / "assets" / "marca_video.png"
                        ruta_thumb = str(ruta_thumb) if ruta_thumb else str(mini)

                    # Crear Widget
                    widget = WidgetGaleria(ruta_completa, hash_archivo, miniatura, tamano, ruta_thumb)
                    #widget.filepath = ruta_completa
                    widget.seleccionado.connect(self._galeria_checkbox_cambiado)

                    self.tablaClasificacion.setCellWidget(fila_actual, col, widget)

                    col += 1
                    if col == NUM_COLS:
                        col = 0
                        fila_actual += 1
                
                # Si la última fila no estaba completa, pasar a la siguiente
                if col != 0:
                    fila_actual += 1

            # Ajustes visuales
            valor = tamano if miniatura else 50

            for r in range(self.tablaClasificacion.rowCount()):
                item = self.tablaClasificacion.item(r, 0)
                if item and item.data(Qt.UserRole) == "header":
                    self.tablaClasificacion.setRowHeight(r, 28)
                else:
                    self.tablaClasificacion.setRowHeight(r, valor)

            for c in range(NUM_COLS):
                self.tablaClasificacion.setColumnWidth(c, tamano)

        except Exception as e:
            self.tablaClasificacion.clear()
            print(f'Error al cargar galeria: {e}')

    def cargar_galeria(self, ruta, miniatura, tamano=100):
        try:
            ARCHIVOS_SEL.clear()
            self.numArcSel = 0
            self.labelArcSelCla.setText(f'{self.numArcSel} archivo/s seleccionados.')

            archivos = os.listdir(ruta)
            NUM_COLS = 7 if tamano == 180 else 13

            # 1️⃣ Agrupar archivos por fecha completa
            from collections import defaultdict
            grupos = defaultdict(list)

            for archivo in archivos:
                ruta_completa = os.path.join(ruta, archivo)

                # Obtener fecha completa para agrupar
                fecha_completa = self.obtener_fecha_json(ruta_completa, self.data)
                grupos[fecha_completa].append(ruta_completa)

            # Ordenar por fecha
            grupos = dict(sorted(grupos.items()))

            # 2️⃣ Preparar la tabla
            self.tablaClasificacion.clearContents()
            self.tablaClasificacion.setColumnCount(NUM_COLS)

            # Mapa fecha > fila del header (para búsqueda rápida)
            self._fila_por_fecha = {}

            fila_actual = 0

            # 3️⃣ Dibujar encabezados + miniaturas

            for fecha, lista_archivos in grupos.items():

                # ---- Encabezado de fecha ----
                self.tablaClasificacion.insertRow(fila_actual)

                # Si la ruta contiene 'Sin_GPS' -> dibujar encabezado
                if 'Sin_GPS' in ruta:

                    # Widget con checkbox + fecha
                    header_widget = HeaderWidget(fecha)
                    header_widget.toggled.connect(self._seleccionar_grupo)

                    # Expandir encabezado a todas las columnas
                    self.tablaClasificacion.setCellWidget(fila_actual, 0, header_widget)
                    self.tablaClasificacion.setSpan(fila_actual, 0, 1, NUM_COLS)

                    # Marcar TODA la fila como header
                    for col in range(NUM_COLS):
                        item_header = QTableWidgetItem()                
                        item_header.setData(Qt.UserRole, "header") # Para saber que fila es encabezado
                        # Evitar selección de la fila header
                        item_header.setFlags(Qt.ItemIsEnabled)
                        self.tablaClasificacion.setItem(fila_actual, col, item_header)

                    # Guardar fila del header
                    self._fila_por_fecha[fecha] = fila_actual

                    fila_actual += 1 # Avenzar después del encabezado
                col = 0

                # ---- Miniaturas del día ----
                for archivo in lista_archivos:

                    if col == 0:
                        self.tablaClasificacion.insertRow(fila_actual)

                    ruta_completa = os.path.join(ruta, archivo)

                    # Obtener hash
                    hash_archivo = calcular_hash_md5(ruta_completa)

                    # Miniatura si es video
                    ruta_thumb = None
                    if archivo.lower().endswith(extensiones_validas("video")):
                        ruta_thumb = self.obtener_ruta_miniatura(hash_archivo)
                        # Usar miniatura
                        mini = Path(__file__).parent.parent / "assets" / "marca_video.png"
                        ruta_thumb = str(ruta_thumb) if ruta_thumb else str(mini)

                    # Crear Widget
                    widget = WidgetGaleria(ruta_completa, hash_archivo, miniatura, tamano, ruta_thumb)
                    #widget.filepath = ruta_completa
                    widget.seleccionado.connect(self._galeria_checkbox_cambiado)

                    self.tablaClasificacion.setCellWidget(fila_actual, col, widget)

                    col += 1
                    if col == NUM_COLS:
                        col = 0
                        fila_actual += 1
                
                # Si la última fila no estaba completa, pasar a la siguiente
                if col != 0:
                    fila_actual += 1

            # Ajustes visuales
            valor = tamano if miniatura else 50

            for r in range(self.tablaClasificacion.rowCount()):
                item = self.tablaClasificacion.item(r, 0)
                if item and item.data(Qt.UserRole) == "header":
                    self.tablaClasificacion.setRowHeight(r, 28)
                else:
                    self.tablaClasificacion.setRowHeight(r, valor)

            for c in range(NUM_COLS):
                self.tablaClasificacion.setColumnWidth(c, tamano)

        except Exception as e:
            self.tablaClasificacion.clear()
            print(f'Error al cargar galeria: {e}')

    def _seleccionar_grupo(self, fecha, estado):
        tabla = self.tablaClasificacion

        # Buscar fila del header por mapa
        fila = self._fila_por_fecha.get(fecha)
        if fila is None:
            return
        
        # Recorrer filas hasta el siguiente header
        r = fila + 1
        row_count = tabla.rowCount()
        while r < row_count:
            item = tabla.item(r, 0)
            if item and item.data(Qt.UserRole) == "header":
                break

            for c in range(tabla.columnCount()):
                widget = tabla.cellWidget(r, c)
                if not widget:
                    continue

                # Intentar varios métodos para marcar la miniatura
                try:
                    # Bloquear señales para evitar recursión
                    widget.blockSignals(True)
                    if hasattr(widget, "setSeleccionado"):
                        widget.setSeleccionado(estado)
                    elif hasattr(widget, "checkbox"):
                        widget.checkbox.setChecked(estado)
                    elif hasattr(widget, "setChecked"):
                        widget.setchecked(estado)
                    else:
                        pass
                    self.numArcSel = self.contar_seleccionados()
                    self.labelArcSelCla.setText(f'{self.numArcSel} archivo/s seleccionados.')

                finally:
                    widget.blockSignals(False)

            r += 1

    def obtener_fecha_json(self, ruta_archivo, data):
        hash_archivo = calcular_hash_md5(ruta_archivo)

        for item in data["pendientes"]["items"]:
            if item["hash"] == hash_archivo:
                return item.get("fecha_completa", "0000-00-00")

    def obtener_ruta_miniatura(self, hash):
        ruta = get_ruta_miniaturas() / f"{hash}.jpg"
        return ruta if ruta.exists() else None
    
    def _galeria_checkbox_cambiado(self, widget, checked):
        self.numArcSel = self.contar_seleccionados()
        if checked:
            ARCHIVOS_SEL[widget.ruta] = widget.hash
        else:
            ARCHIVOS_SEL.pop(widget.ruta, None)

        self.labelArcSelCla.setText(f'{self.numArcSel} archivo/s seleccionados.')

    def contar_seleccionados(self):
        tabla = self.tablaClasificacion
        total = 0

        for r in range(tabla.rowCount()):
            # Saltar filas de encabezado
            item = tabla.item(r, 0)
            if item and item.data(Qt.UserRole) == "header":
                continue

            for c in range(tabla.columnCount()):
                widget = tabla.cellWidget(r, c)

                # Solo contar widgets reales
                if not widget:
                    continue

                # Solo contar si tiene checkbox
                if hasattr(widget, "chk") and widget.chk.isChecked():
                    total += 1

        return total

    # ============================================================
    # UTILIDADES
    # ============================================================
    def obtener_archivo(self, row_index, col=None):
        '''
        Devuelve (ruta, hash) tanto si la tabla es clásica como si es una
        galeria.
        '''

        # 1. Si es tabla clásica (columnas reales)
        if self.vista_actual == 0:
            ruta = self.tabla.model().data(self.tabla.model().index(row_index, 2))
            hash_val = self.tabla.model().data(self.tabla.model().index(row_index, 4))
            return ruta, hash_val
        
        # 2. Si es galería (widgets en celdas)
        if col is None:
            raise ValueError("En modo galería debes pasar row y col")
        
        widget = self.tablaClasificacion.cellWidget(row_index, col)
        if widget is None:
            return None, None
        
        return widget.ruta, widget.hash

    def directorio_vacio(self, path):
        with os.scandir(path) as it:
            for _ in it:
                return False
        return True

    def cargar_pendientes(self):
        data = cargar_json_unico(self.ruta_json)
        total = len(data["pendientes"]["items"])
        self.pendientes_actualizados.emit(total)

    def actualizar_contador_pendientes(self):
        total = len(self.data["pendientes"]["items"])
        self.pendientes_actualizados.emit(total)

    def _reenviar_pendientes(self, total):
        self.pendientes_actualizados.emit(total)

    def mapa_generado(self):
        if hasattr(self, "spinner"):
            self.spinner.close()
            self.view.load(QUrl.fromLocalFile(os.path.abspath(get_ruta_mapa_fotos_html())))
            QMessageBox.information(None, "Mapa actualizado", "El mapa ha sido generado correctamente.")

        self.set_mapa_habilitado(True)
        self.contar_pendientes()

        config_manager.settings.setValue("Estado/mapa_generado", "True")
        config_manager.settings.sync()

    def pregunta_generar_mapa(self):
        respuesta = QMessageBox.question(
            None,
            "Actualizar mapa",
            "¿Quieres genera el mapa ahora?\n\n"
            "Si eliges NO, podrás seguir moviendo/borrardo archivos más rápido.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return respuesta
    