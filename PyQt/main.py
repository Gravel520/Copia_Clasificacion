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
'''

import sys, os
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from componentes.controles import Button

ruta_mapas = './PyQt/mapas/'
meses = ('Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre')

class Bridge(QObject):
    def __init__(self, tableWidget):
        super().__init__()
        self.tabla = tableWidget

    @pyqtSlot(str)
    def recibirRuta(self, ruta):
        if os.path.isdir(ruta):
            archivos = os.listdir(ruta)
            self.tabla.setRowCount(len(archivos))
            self.tabla.setColumnCount(3)
            self.tabla.setHorizontalHeaderLabels(['Nombre de Archivo', 'Ruta', 'Acción'])
            self.tabla.setColumnWidth(0, 205)
            self.tabla.setColumnWidth(2, 140)
            self.tabla.setColumnHidden(1, True)

            for i, nombre in enumerate(archivos):
                ruta_completa = os.path.join(ruta, nombre)

                # Insertar en la tabla.
                self.tabla.setItem(i, 0, QTableWidgetItem(nombre))
                self.tabla.setItem(i, 1, QTableWidgetItem(ruta_completa))
                self.tabla.setCellWidget(i, 2, self.botones_accion(i))
                self.tabla.setRowHeight(i, 30)

        else:
            QMessageBox.warning(None, "Error", f"No se encontró el directorio:\n{ruta}")

    def botones_accion(self, row):
        widget = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        # Creamos los botones.
        copiar_button = Button('copy', '#d3d3d3')
        copiar_button.setToolTip('Copiar Foto')
        compartir_button = Button('share','#add8e6')
        compartir_button.setToolTip('Compartir Foto')
        borrar_button = Button('delete', '#f08080')
        borrar_button.setToolTip('Borrar Foto')

        # Conectamos cada botón a su función
        copiar_button.clicked.connect(lambda _, r=row: self.copiar(r))
        compartir_button.clicked.connect(lambda _, r=row: self.compartir(r))
        borrar_button.clicked.connect(lambda _, r=row: self.borrar(r))

        # Creamos el layout y añadimos los botones
        buttons_layout.addWidget(copiar_button)
        buttons_layout.addWidget(compartir_button)
        buttons_layout.addWidget(borrar_button)

        # Creamos el frame que contendrá el layout
        widget.setLayout(buttons_layout)

        # Asignamos las señal a cada botón.

        return widget
    
    def copiar(self, row):
        archivo = self.obtener_archivo(row)
        print(f'Copiar: {archivo}')

    def compartir(self, row):
        archivo = self.obtener_archivo(row)
        print(f'Compartir: {archivo}')

    def borrar(self, row):
        archivo = self.obtener_archivo(row)
        print(f'Borrar: {archivo}')
    
    def obtener_archivo(self, row_index):
        ruta_id_index = self.tabla.model().index(row_index, 1)
        return self.tabla.model().data(ruta_id_index)        

class MapaWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = uic.loadUi("./PyQt/ui_files/MainWindow.ui")
        self.ui.showMaximized()

        # Visor web
        self.view = QWebEngineView()
        self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{ruta_mapas}mapa_fotos.html")))

        # Canal web
        self.channel = QWebChannel()
        self.bridge = Bridge(self.ui.tableWidget)
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

        ruta_archivo = self.ui.tableWidget.item(row, 1).text()
        pixmap = QPixmap(ruta_archivo)
        if not pixmap.isNull():
            self.ui.labelVisor.setPixmap(pixmap)
            self.ui.labelVisor.setScaledContents(True)
            self.obtener_fecha(ruta_archivo)

        else:
            print("No se pudo cargar la imagen:", ruta_archivo)

    def obtener_fecha(self, dato):
        dato = dato.split(')')[2][1:]
        ano = dato[0:4]
        mes = meses[int(dato[5:]) - 1]
        self.ui.labelFechaListado.setText(f'{mes} de {ano}')

    def signs_controls(self):
        self.ui.tableWidget.itemClicked.connect(self.mostrar_foto)

def main():
    app = QApplication(sys.argv)
    ventana = MapaWindow()
    ventana.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
