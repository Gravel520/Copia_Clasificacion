'''

'''

import os, re
import shutil
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QMessageBox, QFileDialog, QDialog
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from componentes.controles import Button, CheckBox, SpinnerOverlay, SelectorCarpeta
from copia_clasificador_fotos import cargar_json_unico, guardar_json_unico, actualizar_stats
from mapa_generator import extraer_ciudad
from config import *
from worker.mapa_worker import MapaWorker

ARCHIVOS_SEL = {} # clave: ruta_archivo, valor: hash_archivo

class Bridge(QObject):
    actualizarFoto = pyqtSignal(str) # Señal que envia la ruta
    pendientes_actualizados = pyqtSignal(int)

    def __init__(self,
                 tableWidget,
                 labelFechaListado,
                 button_sel_multiple,
                 view,
                 labelFoto,
                 ruta_json):
        super().__init__()
        self.tabla = tableWidget
        self.label = labelFechaListado
        self.boton = button_sel_multiple
        self.view = view
        self.labelFoto = labelFoto
        self.ruta_json = ruta_json
        self.actual_ruta = None

    @pyqtSlot(str)
    def recibirRuta(self, ruta):
        self.actual_ruta = ruta
        self.actualizar_tabla()

    def actualizar_tabla(self):
        ARCHIVOS_SEL.clear()

        # Cargar JSON unificado.
        self.data = cargar_json_unico(RUTA_JSON_UNICO)

        # Extraer listas internas.
        self.historial = self.data["clasificados"]["items"]
        self.eliminado = self.data["eliminados"]["items"]
        self.pendientes = self.data["pendientes"]["items"]

        if self.actual_ruta != None:
            if os.path.isdir(self.actual_ruta):

                archivos = os.listdir(self.actual_ruta)
                self.numero_archivos = len(archivos)

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
                    ['Sel','Nombre de Archivo', 'Ruta', 'Acción', 'Hash']
                )
                
                # Cambiamos el tamaño de la columna del nombre
                #   para que quepa el scrollbar a la derecha.
                tamaño = 185 if self.numero_archivos > 8 else 205
                self.tabla.setColumnWidth(0, 40)
                self.tabla.setColumnWidth(1, tamaño)
                self.tabla.setColumnWidth(3, 140)

                self.tabla.setColumnHidden(0, True)
                self.tabla.setColumnHidden(2, True)
                self.tabla.setColumnHidden(4, True)

                # Configuramos la selección en la tabla.
                self.tabla.setSelectionBehavior(QAbstractItemView.SelectItems) # Sólo celdas individuales
                self.tabla.horizontalHeader().setSectionsClickable(False) # Desactivar la selección de la columna

                mes, ano, lugar = self.obtener_fecha_lugar(self.actual_ruta)
                texto = 'Pendientes' if ano == '0000' else f'{lugar}\n{mes} de {ano}'
                self.label.setText(texto)

                for i, nombre in enumerate(archivos):

                    ruta_completa = os.path.join(self.actual_ruta, nombre)
                    # Buscar el diccionario que coincide para obtener el hash
                    ruta_conver = ruta_completa.replace('/', '\\') # Conversión para que coincide con datos .json

                    # Elegir lista según si es pendiente o clasificado.
                    busqueda_hash = (
                        self.pendientes
                        if '(Sin_GPS)' in ruta_conver
                        else self.historial
                    )
                    coincidencia = next(
                        (r for r in busqueda_hash if r['ruta'] == ruta_conver), 
                        None
                    )

                    hash = coincidencia['hash'] if coincidencia else ""

                    # Insertar en la tabla.
                    self.tabla.setCellWidget(i, 0, self.boton_checkbox(i))
                    self.tabla.setItem(i, 1, QTableWidgetItem(nombre))
                    self.tabla.setItem(i, 2, QTableWidgetItem(ruta_completa))
                    self.tabla.setCellWidget(i, 3, self.botones_accion(i))
                    self.tabla.setItem(i, 4, QTableWidgetItem(hash))
                    self.tabla.setRowHeight(i, 30)

            else:
                QMessageBox.warning(None, "Error", f"No se encontró el directorio:\n{self.actual_ruta}")

            if self.tabla.rowCount() > 0:
                # Selecciona la primera fila y primera columna para que cambie
                #   al color de selección, azul.
                self.tabla.setCurrentCell(0, 1)
                # Obtenemos la ruta del archivo que está en la columna 2.
                ruta_archivo = self.tabla.item(0, 2).text()
                # Emitir la señal para que MainWindow muestre la foto
                self.actualizarFoto.emit(ruta_archivo)

    def boton_checkbox(self, row):
        check = QWidget()
        sel_check = CheckBox()
        check_layout = QHBoxLayout()
        check_layout.setContentsMargins(0, 0, 0, 0)
        sel_check.stateChanged.connect(lambda state, r=row: self.state_change_ckeckbox(r, state))
        check_layout.addWidget(sel_check)
        check_layout.setAlignment(Qt.AlignCenter)
        check.setLayout(check_layout)
        return check

    def botones_accion(self, row):
        widget = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # Creamos los botones.
        copiar_button = Button('copy', '#B2B3AD')
        copiar_button.setToolTip('Copiar Foto')
        mover_button = Button('move', '#AEB626')
        mover_button.setToolTip('Mover Foto')
        compartir_button = Button('share','#0BAFBA')
        compartir_button.setToolTip('Compartir Foto')
        borrar_button = Button('delete', '#f08080')
        borrar_button.setToolTip('Borrar Foto')        

        # Conectamos cada botón a su función
        copiar_button.clicked.connect(lambda _, r=row: self.copiar(r))
        mover_button.clicked.connect(lambda _, r=row: self.mover(r))
        compartir_button.clicked.connect(lambda _, r=row: self.compartir(r))
        borrar_button.clicked.connect(lambda _, r=row: self.borrar(r))

        # Creamos el layout y añadimos los botones
        buttons_layout.addWidget(copiar_button)
        buttons_layout.addWidget(mover_button)
        buttons_layout.addWidget(compartir_button)
        buttons_layout.addWidget(borrar_button)

        # Creamos el frame que contendrá el layout
        widget.setLayout(buttons_layout)

        return widget
        
    def obtener_fecha_lugar(self, dato):
        fecha = dato.split(')')[2][1:]
        lugar = dato.split('(')[1].split(')')[0]
        ano = fecha[0:4]
        mes = MESES[int(fecha[5:]) - 1]
        return mes, ano, lugar
    
    def state_change_ckeckbox(self, row, state_int):
        ruta_archivo, hash_archivo = self.obtener_archivo(row)
        state = Qt.CheckState(state_int)

        if state == Qt.Checked:
            ARCHIVOS_SEL[ruta_archivo] = hash_archivo
        elif state == Qt.Unchecked:
            ARCHIVOS_SEL.pop(ruta_archivo, None)
    '''
    Función para copiar el o los archivos seleccionados a una carpeta de
    destino, elegida por el usuario mediante un cuadro de diálogo.
    '''
    def copiar(self, row):
        # Selección de la carpeta de destino. Abre el selector de carpetas.
        # El argumento 'None' es porque no hereda de un QWidget, ya que hereda
        #   de 'Bridge'.
        carpeta_destino = QFileDialog.getExistingDirectory(None, "Seleccionar carpeta de destino")
        if not carpeta_destino:
            return # El usuario canceló.
        
        # Obtenemos la lista de los archivos o el archivo a copiar.
        if not ARCHIVOS_SEL:
            ruta_archivo, hash_archivo = self.obtener_archivo(row)
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

    def mover(self, row):
        carpeta_destino = ''
        dlg = SelectorCarpeta(self.actual_ruta, None)

        if dlg.exec_() == QDialog.Accepted:
            carpeta_destino = dlg.carpeta_seleccionada()
        
        if not carpeta_destino:
            return # El usuario canceló.
        
        # Cargar JSON unificado
        self.data = cargar_json_unico(RUTA_JSON_UNICO)
        self.historial = self.data["clasificados"]["items"]
        self.pendientes = self.data["pendientes"]["items"]

        # Obtenemos la lista de los archivos o el archivo a mover.
        if not ARCHIVOS_SEL:            
            ruta_archivo, hash_archivo = self.obtener_archivo(row)
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

                entrada["ubicacion"] = f"({ciudad})({pais})"
                entrada["fecha"] = f"({fecha})"
                
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
        guardar_json_unico(RUTA_JSON_UNICO, self.data)

        # Emitir actualización de pendientes.
        self.actualizar_contador_pendientes()

        if self.directorio_vacio(origen):
            os.rmdir(origen)
            self.tabla.clearContents()
            self.labelFoto.setPixmap(QPixmap())
            self.actual_ruta = None

        # Mensaje final
        if errores:
            mensaje = "Algunos archivos no se pudiero mover: \n\n"
            mensaje += "\n".join(f"{a}: {err}" for a, err in errores)
            QMessageBox.warning(None, "Errores al mover", mensaje)
        else:
            QMessageBox.information(None, "Acción completada", "Todos los archivos fueron\nmovidos correctamente.")

        self.spinner = SpinnerOverlay(self.view)
        self.spinner.show()

        self.worker = MapaWorker()
        self.worker.pendientes_actualizados.connect(self._reenviar_pendientes)
        self.worker.terminado.connect(self.mapa_generado)
        self.worker.start()

        self.actualizar_tabla()

    def seleccionar_directorio_destino(self):
        # Seleccionamos la carpeta de destino. Abre el selector de directorios.
        # El argumento 'None' es porque no hereda de un QWidget, ya que hereda
        #   de 'Bridge'.
        carpeta_destino = QFileDialog.getExistingDirectory(None, "Seleccionar carpeta de destino")
        if not carpeta_destino:
            return None
        
        # Normalizamos rutas
        carpeta_destino = os.path.abspath(carpeta_destino)

        # Comprobar que están en el mismo drive.
        if os.path.splitdrive(carpeta_destino)[0].lower() != os.path.splitdrive(RUTA_PRINCIPAL)[0].lower():
            QMessageBox.warning(None, "Directorio inválido",
                                f"Debe seleccionar un directorio dentro de:\n{RUTA_PRINCIPAL}")
            return None

        # Comprobamos que destino está dentro del principal
        if os.path.commonpath([carpeta_destino, RUTA_PRINCIPAL]) == RUTA_PRINCIPAL:
            return carpeta_destino
        else:
            QMessageBox.warning(None, "Directorio inválido",
                                f"Debe seleccionar un directorio dentro de:\n{RUTA_PRINCIPAL}")
            return None        

    def mapa_generado(self):
        self.spinner.movie.stop()
        self.spinner.close()
        self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{RUTA_MAPA_HTML}")))
        QMessageBox.information(None, "Mapa actualizado", "El mapa ha sido generado correctamente.")

    def compartir(self, row):
        archivo = self.obtener_archivo(row)
        print(f'Compartir: {archivo}')

    def borrar(self, row):
        mensaje = 'Archivo(s):\n'

        # Cargar JSON unificado.
        self.data = cargar_json_unico(RUTA_JSON_UNICO)
        self.historial = self.data["clasificados"]["items"]
        self.pendientes = self.data["pendientes"]["items"]
        self.eliminado = self.data["eliminados"]["items"]

        # Obtenemos la lista de los archivos o el archivo a borrar.
        if not ARCHIVOS_SEL:
            ruta_archivo, hash_archivo = self.obtener_archivo(row)
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

                print(f"{archivo} ❌ Borrado...")

            except Exception as e:
                print(f'Error al borrar {archivo}: {e}')

        QMessageBox.information(None, "Borrado de archivos", "Borrado Completado con éxito.")

        # Actualizar estadístitcas.
        self.data["stats"]["total_clasificados"] = len(self.historial)
        self.data["stats"]["total_pendientes"] = len(self.pendientes)
        self.data["stats"]["total_eliminados"] = len(self.eliminado)

        # Guardar JSON unificado.
        guardar_json_unico(RUTA_JSON_UNICO, self.data)

        # Emitir actualización de pendientes.
        self.actualizar_contador_pendientes()

        # Comprobamos si existe el directorio para actualizar la
        #   tabla o no.
        if self.directorio_vacio(origen):
            os.rmdir(origen)
            self.tabla.clearContents()
            self.labelFoto.setPixmap(QPixmap())
            self.actual_ruta = None            

        self.spinner = SpinnerOverlay(self.view)
        self.spinner.show()

        self.worker = MapaWorker()
        self.worker.pendientes_actualizados.connect(self._reenviar_pendientes)
        self.worker.terminado.connect(self.mapa_generado)
        self.worker.start()

        self.actualizar_tabla()

    def origen_de_seleccion(self, row):
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
            ruta_archivo, _ = self.obtener_archivo(row)
            return os.path.dirname(os.path.abspath(ruta_archivo))
    
    def obtener_archivo(self, row_index):
        ruta_id_index = self.tabla.model().index(row_index, 2)
        ruta_archivo = self.tabla.model().data(ruta_id_index)
        hash_id_index = self.tabla.model().index(row_index, 4)
        hash_archivo = self.tabla.model().data(hash_id_index)
        return ruta_archivo, hash_archivo
    
    def directorio_vacio(self, path):
        with os.scandir(path) as it:
            for _ in it:
                return False
        return True
    
    def cargar_pendientes(self):
        data = cargar_json_unico(self.ruta_json)

        pendientes = data["pendientes"]["items"]
        total = len(pendientes)

        self.pendientes_actualizados.emit(total)

    def actualizar_contador_pendientes(self):
        total = len(self.data["pendientes"]["items"])
        self.pendientes_actualizados.emit(total)

    def _reenviar_pendientes(self, total):
        # Reemite la señal hacia fuera (MainWindow ya está conectado a esta)
        self.pendientes_actualizados.emit(total)
