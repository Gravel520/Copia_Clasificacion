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

import sys, os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QMessageBox, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from componentes.controles import ScrollableMessageBox, SpinnerOverlay
from config import *
from worker.mapa_worker import MapaWorker
from worker.copia_worker import CopiaWorker
from bridge_.bridge import Bridge

ARCHIVOS_SEL = {} # clave: ruta_archivo, valor: hash_archivo

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
        self.bridge = Bridge(self.ui.tableWidget, 
                            self.ui.labelFechaListado,
                            self.ui.button_sel_multiple,
                            self.view,
                            self.ui.labelVisor,
                            RUTA_JSON_UNICO)
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Conectar señal de Bridge con método mostrar_foto
        self.bridge.actualizarFoto.connect(self.mostrar_foto)

        self.bridge.pendientes_actualizados.connect(self.actualizar_menu_pendientes)

        layout = QVBoxLayout(self.ui.QWidget_foto)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.view)

        # Actualizar menú al abrir
        self.bridge.cargar_pendientes()

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
        self.worker_copia.start()

    def copia_finalizada(self, mensaje):
        self.spinner.movie.stop()
        self.spinner.close()

        if mensaje == '': return

        # Ajustamos el tamaño del ScrollableMessageBox, según el número
        #   de líneas y la longitud de las mismas.
        ancho, alto = self.analizar_mensaje(mensaje)
        num_copiados = alto # Obtenemos el número de archivos según el número de líneas del mensaje.
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
            self.worker_mapa.pendientes_actualizados.connect(self.bridge._reenviar_pendientes)
            self.worker_mapa.terminado.connect(self.mapa_finalizado)
            self.worker_mapa.start()
            
    def mapa_finalizado(self):
            self.spinner.movie.stop()
            self.spinner.close()
            self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{RUTA_MAPA_HTML}")))
            QMessageBox.information(self, "Mapa actualizado", "El mapa ha sido generado correctamente. ")
            
    # Función para habilitar o no la acción del menú 'Clasificar' (Pendientes),
    #   que nos dirá si hay archivos pendientes de clasificar y cuantos.
    def actualizar_menu_pendientes(self, total):
        # Actualizar texto
        self.ui.actionPendientes.setText(f'Pendientes ({total})')

        # Habilitar solo si hay elementos
        self.ui.actionPendientes.setEnabled(total > 0)

    def clasificar_pendientes(self):
        self.bridge.cargar_pendientes()
        self.bridge.recibirRuta("E:\\BackupFotos\\(Sin_GPS)(Sin_GPS)(0000-00)")

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
        self.ui.actionPendientes.triggered.connect(self.clasificar_pendientes)
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
