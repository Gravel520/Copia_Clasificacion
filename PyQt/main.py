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
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox, QFileDialog
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSlot, QUrl

ruta_mapas = './PyQt/'

class Bridge(QObject):
    @pyqtSlot(str)
    def recibirRuta(self, ruta):
        if os.path.isdir(ruta):
            archivos = os.listdir(ruta)
            texto = "\n".join(archivos)
            QMessageBox.information(None, f"Archivos en {ruta}", texto)
            archivo, _ = QFileDialog.getOpenFileName(
                None,
                "Selecciona un archivo",
                ruta,
                "Imágen (*.jpg *.jpeg );;Video (*.mp4)"
            )
            print(f'Archivo elegido: {archivo}')
        else:
            QMessageBox.warning(None, "Error", f"No se encontró el directorio:\n{ruta}")

class MapaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mapa de Fotos")
        self.resize(1000, 700)

        # Visor web
        self.view = QWebEngineView()
        self.view.load(QUrl.fromLocalFile(os.path.abspath(f"{ruta_mapas}mapa_fotos.html")))

        # Canal web
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Layout
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self.view)
        self.setCentralWidget(central)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MapaWindow()
    ventana.show()
    sys.exit(app.exec_())
