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
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWidgets import QTableWidgetItem, QAbstractItemView
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from componentes.controles import Button, CheckBox, Button_Sel

RUTA_MAPA_HTML = './PyQt/mapas/mapa_fotos.html'
RUTA_UI = './PyQt/ui_files/MainWindow.ui'
MESES = (
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
     'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
)
ARCHIVOS_SEL = []

class Bridge(QObject):
    def __init__(self, tableWidget, labelFechaListado, button_sel_multiple):
        super().__init__()
        self.tabla = tableWidget
        self.label = labelFechaListado
        self.boton = button_sel_multiple

    @pyqtSlot(str)
    def recibirRuta(self, ruta):
        ARCHIVOS_SEL.clear()
        if os.path.isdir(ruta):
            archivos = os.listdir(ruta)
            self.numero_archivos = len(archivos)
            self.tabla.setRowCount(self.numero_archivos)
            self.tabla.setColumnCount(4)
            self.tabla.setStyleSheet("""
                QTableWidget::item {
                    border: none;
                    padding: 0px;
                    margin: 0px;
                }
            """)
            self.tabla.setHorizontalHeaderLabels(['Sel','Nombre de Archivo', 'Ruta', 'Acción'])
            # Cambiamos el tamaño de la columna del nombre
            #   para que quepa el scrollbar a la derecha.
            tamaño = 185 if self.numero_archivos > 8 else 205
            self.tabla.setColumnWidth(0, 40)
            self.tabla.setColumnWidth(1, tamaño)
            self.tabla.setColumnWidth(3, 140)
            self.tabla.setColumnHidden(0, True)
            self.tabla.setColumnHidden(2, True)
            # Configuramos la selección en la tabla.
            self.tabla.setSelectionBehavior(QAbstractItemView.SelectItems) # Sólo celdas individuales
            self.tabla.setSelectionMode(QAbstractItemView.SingleSelection) # Sólo una celda a la vez
            self.tabla.horizontalHeader().setSectionsClickable(False) # Desactivar la selección de la columna

            mes, ano = self.obtener_fecha(ruta)
            self.label.setText(f'{mes} de {ano}')

            for i, nombre in enumerate(archivos):
                ruta_completa = os.path.join(ruta, nombre)

                # Insertar en la tabla.
                self.tabla.setCellWidget(i, 0, self.boton_checkbox(i))
                self.tabla.setItem(i, 1, QTableWidgetItem(nombre))
                self.tabla.setItem(i, 2, QTableWidgetItem(ruta_completa))
                self.tabla.setCellWidget(i, 3, self.botones_accion(i))
                self.tabla.setRowHeight(i, 30)

        else:
            QMessageBox.warning(None, "Error", f"No se encontró el directorio:\n{ruta}")

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
        ruta_id_index = self.tabla.model().index(row, 2)
        ruta_archivo = self.tabla.model().data(ruta_id_index)
        state = Qt.CheckState(state_int)

        if state == Qt.Checked:
            if ruta_archivo not in ARCHIVOS_SEL:
                ARCHIVOS_SEL.append(ruta_archivo)
        elif state == Qt.Unchecked:
            if ruta_archivo in ARCHIVOS_SEL:
                ARCHIVOS_SEL.remove(ruta_archivo)
    
    def copiar(self, row):
        if ARCHIVOS_SEL:
            print('Copiar archivos:')
            for archivo in ARCHIVOS_SEL:
                print(archivo)
        else:
            archivo = self.obtener_archivo(row)
            print(f'Copiar: {archivo}')

    def mover(self, row):
        archivo = self.obtener_archivo(row)
        print(f'Mover: {archivo}')

    def compartir(self, row):
        archivo = self.obtener_archivo(row)
        print(f'Compartir: {archivo}')

    def borrar(self, row):
        archivo = self.obtener_archivo(row)
        print(f'Borrar: {archivo}')
    
    def obtener_archivo(self, row_index):
        ruta_id_index = self.tabla.model().index(row_index, 2)
        return self.tabla.model().data(ruta_id_index)
    
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
        self.bridge = Bridge(self.ui.tableWidget, self.ui.labelFechaListado, self.ui.button_sel_multiple)
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        layout = QVBoxLayout(self.ui.QWidget_foto)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.view)

        self.signs_controls()

    def show(self):
        self.ui.show()

    def mostrar_foto(self):
        row = self.ui.tableWidget.currentRow()

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

    def signs_controls(self):
        self.ui.tableWidget.itemClicked.connect(self.mostrar_foto)
        self.ui.tableWidget.currentItemChanged.connect(self.mostrar_foto)
        self.ui.button_sel_multiple.clicked.connect(self.columna_seleccion)
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
