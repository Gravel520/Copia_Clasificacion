'''
Script en Python.
Este código crea una aplicación de escritorio con PyQt5 que muestra una
página web (HTML) en una ventana, y permite que esa página se comunique
con Python para abrir un cuadro de diálogo de archivos desde una ruta
concreta.

IMPORTACIONES:
QWebEngineView - Permite mostrar contenido web (HTML) dentro de una app.
QWebChannel - Establece un canal de comunicación entre JavaScript (HTML)
    y Python.
QObject, pyqtSlot, QUrl -   Clase base para objetos Qt.
                            Decorador que expone métodos a JavaScript.
                            Para manejar URLs locales o remotas.

CLASE Bridge:
Es un puente entre JavaScript y Python.
Con '@pyqtSlot(str)' indicamos que este método puede ser llamado desde
JavaScript con un argumento tipo str.
La lógica del método 'recibirRuta', es que primero verificamos si la
    ruta recibida es un directorio válido. De ser así, obtenemos todos
    los archivos que contiene ese directorio y los presentamos en una
    ventana emergente, en una lista. Una vez cerrada esta ventana se
    abre un cuadro de diálogo para seleccionar un archivos que esta en
    esa ruta, filtrando por imágenes y videos. Por último mostramos el
    archivo seleccionado en la consola (incluida la ruta completa).

CLASE MapaWindow:
Hereda de 'QMainWindow', que es la ventana principal de la app.
Definimos el título y el tamaño de la ventana.
Creamos un visor web (QwebEngineView) y cargamos el archivo HTML local
    que contiene el mapa HTML.
Creamos un canal web 'QWebChannel' y un objeto 'Bridge', que lo registramos
    en el canal y que será accesible desde JavaScript como "bridge". Por
    último añadimos el canal web al visor web, para que haya comunicación.

Finálmente creamos el layout y lanzamos la app.

PROMOCIONAR UN CONTROL DESDE QTDESIGNER:
Cuando creamos un control estandar en QtDesigner y lo queremos instanciar
    desde una clase en Python, tenemos que promocionarlo en Qt Designer,
    de la siguiente forma:
    - Abrir el archivo .ui en Qt Designer.
    - Seleccionar el control a promocionar.
    - Con el botón derecho del ratón seleccionar la opción 'Promote to...'.
    - En los campos:
        * Base class: Tipo de control (QPushButton).
        * Promoted class name: Nombre de la clase (Button_Sel).
        * Header file: Módulo donde está definida la clase en Python
            (componentes/controles.py)
    - Pulsar sobre 'Add'.
    - Pulsar sobre 'Promote'.
    - Finalmente guardar el proyecto .ui.
    Qt Internamente le pasa el 'parent' como argumento adicional, así que
    hay que aceptar este argumento en la clase (Button_Sel):
        def __init__(self, parent=None):
            super().__init__(parent)

Finalmente importamos el módulo normalmente, antes de cargar el archivo .ui.

'''

import sys, os, re
import shutil
import mapa_generator
import copia_clasificador_fotos
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFileDialog, QAction, QProgressDialog, QDialog, QLabel, QComboBox, QPushButton, QListWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl, QThread, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import Qt
from componentes.controles import Button, CheckBox, Button_Sel, ScrollableMessageBox, SpinnerOverlay, SelectorCarpeta
from copia_clasificador_fotos import cargar_json, guardar_json
from mapa_generator import extraer_ciudad
from config import *

DUPLICADOS = HISTORIAL
ELIMINADOS = RUTA_ELIMINADOS
ARCHIVOS_SEL = {} # clave: ruta_archivo, valor: hash_archivo

class MapaWorker(QThread):
    terminado = pyqtSignal()

    def run(self):
        mapa_generator.generar_mapa_desde_historial()
        self.terminado.emit()

class CopiaWorker(QThread):
    terminado = pyqtSignal(str, int) # Mensaje, num_copiados

    def __init__(self, carpeta_origen=None):
        super().__init__()
        self.carpeta_origen = carpeta_origen

    def run(self):
        # Estas líneas son para depurar dentro de los hilos.
        try:
            import debugpy
            debugpy.debug_this_thread()

            try:
                mensaje, num_copiados = copia_clasificador_fotos.main(self.carpeta_origen)
                self.terminado.emit(mensaje, num_copiados)
            except Exception as e:
                # Emitir también en caso de error para que el spinner se detenga.
                self.terminado.emit(f"Error al clasificar : {e}", 0)
                
        except Exception as e:
            self.terminado.emit(f"Error al clasificar : {e}", 0)

class Bridge(QObject):
    actualizarFoto = pyqtSignal(str) # Señal que envia la ruta

    def __init__(self, tableWidget, labelFechaListado, button_sel_multiple, view, labelFoto):
        super().__init__()
        self.tabla = tableWidget
        self.label = labelFechaListado
        self.boton = button_sel_multiple
        self.view = view
        self.labelFoto = labelFoto
        self.actual_ruta = None

    @pyqtSlot(str)
    def recibirRuta(self, ruta):
        self.actual_ruta = ruta
        self.actualizar_tabla()

    def actualizar_tabla(self):
        ARCHIVOS_SEL.clear()
        self.historial = cargar_json(DUPLICADOS)
        self.eliminado = cargar_json(ELIMINADOS)

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
                self.tabla.setHorizontalHeaderLabels(['Sel','Nombre de Archivo', 'Ruta', 'Acción', 'Hash'])
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

                mes, ano = self.obtener_fecha(self.actual_ruta)
                self.label.setText(f'{mes} de {ano}')

                for i, nombre in enumerate(archivos):
                    ruta_completa = os.path.join(self.actual_ruta, nombre)
                    # Buscar el diccionario que coincide para obtener el hash
                    ruta_conver = ruta_completa.replace('/', '\\') # Conversión para que coincide con datos .json
                    coincidencia = next((r for r in self.historial if r['ruta'] == ruta_conver), None)

                    if coincidencia:
                        hash = coincidencia['hash']

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
        
    def obtener_fecha(self, dato):
        dato = dato.split(')')[2][1:]
        ano = dato[0:4]
        mes = MESES[int(dato[5:]) - 1]
        return mes, ano
    
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

                # Actualizar duplicados.json
                for entrada in self.historial:
                    if entrada.get('hash') == hash:
                        destino = destino.replace('/', '\\')
                        entrada["ruta"] = destino
                        parentesis = re.findall(r'\([^)]+\)', destino)
                        resultado = ''.join(parentesis)
                        ciudad, pais, fecha = extraer_ciudad(resultado)
                        entrada["ubicacion"] = f"({ciudad})({pais})"
                        entrada["fecha"] = f"({fecha})"
                        break

            except Exception as e:
                errores.append((archivo, str(e)))
                print(f'Error al mover {archivo}: {e}')

        guardar_json(self.historial, DUPLICADOS)

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
        # Obtenemos la lista de los archivos o el archivo a borrar.
        if not ARCHIVOS_SEL:
            ruta_archivo, hash_archivo = self.obtener_archivo(row)
            ARCHIVOS_SEL[ruta_archivo] = hash_archivo

        for archivo, _ in ARCHIVOS_SEL.items():
            nombre = os.path.basename(archivo)
            mensaje += f"- ({nombre}) ❌ Eliminar?.\n"

        origen = self.origen_de_seleccion(row)

        res = QMessageBox.question(None, f"Borrado de {origen}.", 
                                   mensaje,
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        if res == QMessageBox.Yes:
            for archivo, hash in ARCHIVOS_SEL.items():
                try:
                    os.remove(archivo) # Borramos el archivo físico.
                    # Añadimos el 'hash' al json de eliminados.
                    self.eliminado.append({
                        "hash": hash
                    })
                    # Borramos el registro del json historial
                    for i, entrada in enumerate(self.historial):
                        if entrada.get('hash') == hash:
                            # Eliminamos la entrada completa de la lista.
                            del self.historial[i]
                            break
                    print(f"{archivo} ❌ Borrado...")

                except Exception as e:
                    print(f'Error al mover {archivo}: {e}')

            QMessageBox.information(None, "Borrado de archivos", "Borrado Completado con éxito.")

            guardar_json(self.eliminado, ELIMINADOS)
            guardar_json(self.historial, DUPLICADOS)

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
            self.worker.terminado.connect(self.mapa_generado)
            self.worker.start()

            self.actualizar_tabla()
            
        else:
            QMessageBox.information(None, "Borrado de archivos", "Borrado cancelado por el usuario.")

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

class MapaWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi(RUTA_UI)
        self.ui.showMaximized()

        # Visor web
        self.view = QWebEngineView()
        self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{RUTA_MAPA_HTML}")))

        # Canal web
        self.channel = QWebChannel()
        self.bridge = Bridge(self.ui.tableWidget, self.ui.labelFechaListado, self.ui.button_sel_multiple, self.view, self.ui.labelVisor)
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Conectar señal de Bridge con método mostrar_foto
        self.bridge.actualizarFoto.connect(self.mostrar_foto)

        layout = QVBoxLayout(self.ui.QWidget_foto)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.view)

        self.signs_controls()

    def show(self):
        self.ui.show()

    '''
    Cuando llamamos a esta función desde la señal de Bridge, estamos pasando
    un str con la ruta del archivo, sin embargo, cuando la llamamos desde
    la señal de la tabla 'itemclicked' o 'currentItemChanged' estamos
    pasando directamente un 'QTableWidgetItem' como argumento, con lo cual
    da error porque no es el str de la ruta del archivo.
    Tememos que comprobar si el parámetro recibido es un objeto de tabla o
    un str, para poder obtener desde la columna de la tabla que contiene la
    ruta del archivo, el texto correspondiente.
    '''
    def mostrar_foto(self, item=None):
        if isinstance(item, QTableWidgetItem):
            # Si viene de la señal, obtenemos la fila y la columna de la ruta
            row = item.row()
            ruta_archivo = self.ui.tableWidget.item(row, 2).text()
        else:
            # Si viene de la señal personalizada Bridge o llamada manual
            if isinstance(item, str):
                ruta_archivo = item
            else:
                row = self.ui.tableWidget.currentRow()
                if row < 0:
                    return
                ruta_archivo = self.ui.tableWidget.item(row, 2).text()

        pixmap = QPixmap(ruta_archivo)
        if not pixmap.isNull():
            self.ui.labelVisor.setPixmap(pixmap)
            self.ui.labelVisor.setScaledContents(True)

        else:
            print("No se pudo cargar la imagen:", ruta_archivo)

    # Función para mostrar u ocultar la columna de la selección.
    # Dependiendo del número de registros, la columna del nombre se
    #   hara más pequeña.
    def columna_seleccion(self):
        ARCHIVOS_SEL.clear()
        table = self.ui.tableWidget
        columna = 0 
        columna_oculta = table.isColumnHidden(columna)
        num_filas = table.rowCount()

        if not columna_oculta:
            nueva_visibilidad = True
            ancho_columna_1 = 205
        elif num_filas > 8:
            nueva_visibilidad = False
            ancho_columna_1 = 135
        else:
            nueva_visibilidad = False
            ancho_columna_1 = 155

        table.setColumnHidden(columna, nueva_visibilidad)
        table.setColumnWidth(1, ancho_columna_1)

        # Cada vez que mostremos la columna, desmarcar todos los checkboxes.
        self.checked_unchecked_all_checkbox(nueva_visibilidad, table, columna, num_filas, False)

    # Función para marcar o desmarcar todos los checkbox.
    '''
    Tenemos que acceder al checkbox dentro del contenedor, primero 
    accedemos a la celda, después accedemos al layout y finalmente
    accedemos al control.
    '''
    def checked_unchecked_all_checkbox(self, nueva_visibilidad, table, columna, num_filas, state):
        if not nueva_visibilidad:
            for fila in range(num_filas):
                celda = table.cellWidget(fila, columna) # La celda.
                if celda is not None:
                    layout = celda.layout() # Contenedor del check.
                    if layout is not None and layout.count() > 0:
                        checkbox = layout.itemAt(0).widget() # El checkbox.
                        if checkbox is not None:
                            checkbox.setChecked(state)

    # Función para seleccionar la carpeta origen para la copia/clasificación
    #   de las fotos.
    def select_directory(self):
        carpeta_origen = QFileDialog.getExistingDirectory(self, "Seleccionar directorio de origen")
        if not carpeta_origen:
            return # El usuario canceló.
        self.iniciar_copia(carpeta_origen)

    def select_movil(self):
        self.iniciar_copia(None)

    def iniciar_copia(self, carpeta_origen=None):
        self.spinner = SpinnerOverlay(self)
        self.spinner.show()
        
        self.worker_copia = CopiaWorker(carpeta_origen)
        self.worker_copia.terminado.connect(self.copia_finalizada)
        # ESTO ES TEMPORAL, LO CORRECTO ES START EN LUGAR DE RUN
        self.worker_copia.start()

    def copia_finalizada(self, mensaje, num_copiados):
        self.spinner.movie.stop()
        self.spinner.close()

        if mensaje == '' and num_copiados == 0: return

        # Ajustamos el tamaño del ScrollableMessageBox, según el número
        #   de líneas y la longitud de las mismas.
        ancho, alto = self.analizar_mensaje(mensaje)
        ancho = min(500, 7 * ancho)
        alto = min(600, 18 * alto)        

        if mensaje:
            dlg = ScrollableMessageBox(f"Copia de Archivos: {num_copiados} archivos copiados", mensaje)
        else:            
            dlg = ScrollableMessageBox("Copia de Archivos", "No se pudo realizar la copia, o\nno hay archivos que copiar")
        
        dlg.resize(ancho, alto)
        dlg.exec_()

        # Generar mapa con la nueva información y mostrarlo si se han
        #   copiado algún archivo.
        if num_copiados > 0:
            self.spinner = SpinnerOverlay(self)
            self.spinner.show()

            self.worker_mapa = MapaWorker()
            self.worker_mapa.terminado.connect(self.mapa_finalizado)
            self.worker_mapa.start()
            
    def mapa_finalizado(self):
            self.spinner.movie.stop()
            self.spinner.close()
            self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{RUTA_MAPA_HTML}")))
            QMessageBox.information(self, "Mapa actualizado", "El mapa ha sido generado correctamente. ")

    # Función para obtener el tamaño de ancho y alto del 
    #   ScrollableMessageBox.
    @staticmethod
    def analizar_mensaje(message):
        lineas = message.splitlines()
        num_lineas = len(lineas)
        longitud_maxima = max((len(linea) for linea in lineas), default=0)
        return longitud_maxima, num_lineas

    # Evento para confirmar el fín de la ejecución de la aplicación.
    def closeEvent(self, e):
        reply = QMessageBox.question(self, "Confirmar salida",
                                     "¿Estás seguro de salir de la app?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            QApplication.quit()
        else:
            e.ignore()

    def signs_controls(self):
        self.ui.tableWidget.itemClicked.connect(self.mostrar_foto)
        self.ui.tableWidget.currentItemChanged.connect(self.mostrar_foto)
        self.ui.button_sel_multiple.clicked.connect(self.columna_seleccion)
        self.ui.actionDesde_Ruta.triggered.connect(self.select_directory)
        self.ui.actionDesde_Movil.triggered.connect(self.select_movil)
        self.ui.actionSalir_3.triggered.connect(self.close)
        # Señal para marcar todas las filas de la tabla. Ultimo parámetro (True)
        self.ui.button_sel_multiple.marcarTodos.connect(
            lambda: self.checked_unchecked_all_checkbox(
            False, self.ui.tableWidget, 0, self.ui.tableWidget.rowCount(), True
            ))
        # Señal para desmarcar todas las filas de la tabla. Ultimo parámetro (False)
        self.ui.button_sel_multiple.desmarcarTodos.connect(lambda: self.checked_unchecked_all_checkbox(
            False, self.ui.tableWidget, 0, self.ui.tableWidget.rowCount(), False
            ))

def main():
    app = QApplication(sys.argv)
    ventana = MapaWindow()
    ventana.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
