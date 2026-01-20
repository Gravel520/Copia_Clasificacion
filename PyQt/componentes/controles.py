'''
Script en Python. Contendrá los distintos componentes, controles o 
    widtget creados por nosotros y que vamos a acoplar a la ventana.

Button: QPushButton que forman cada uno de los dos botones que aparecen
    en la tabla de los listados de los archivos de imagen. Como parámetros
    recibe el nombre del icono, y el color del botón.
'''

import os
from PyQt5.QtWidgets import (QWidget, QPushButton, QCheckBox, QMenu,
                             QAction, QDialog, QVBoxLayout, QHBoxLayout, 
                             QTextEdit, QLabel, QApplication, QListWidget)
from PyQt5.QtGui import QIcon, QCursor, QMovie
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtCore import Qt, QRect
from config import RUTA_PRINCIPAL, SPINNER

assets = 'PyQt/assets/'

class Button(QPushButton):
    def __init__(self, icon, color):
        super().__init__()
        self.setFixedSize(24, 24)
        self.setIcon(QIcon(f'{assets}{icon}.png'))
        self.setIconSize(QSize(16, 16))
        self.setStyleSheet(f'''
            QPushButton {{
                color: #e3e3e3;                           
                background-color: {color};
                border: none;
            }}
            QPushButton::hover {{
                background-color: #ffc13b;
            }}
        ''')
        self.setCursor(QCursor(Qt.PointingHandCursor))

class Button_Sel(QPushButton):
    marcarTodos = pyqtSignal()
    desmarcarTodos = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            menu = QMenu(self)

            # Crear acciones con iconos
            marcar = QAction(QIcon(f'{assets}checkbox_checked.png'), "Marcar Todos")
            desmarcar = QAction(QIcon(f'{assets}checkbox_unchecked.png'), "Desmarcar Todos")
            
            menu.addAction(marcar)
            menu.addAction(desmarcar)

            action = menu.exec_(e.globalPos())
            if action == marcar:
                self.marcarTodos.emit()
            elif action == desmarcar:
                self.desmarcarTodos.emit()

        else:
            super().mousePressEvent(e)

class CheckBox(QCheckBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QCheckBox {{
                spacing: 5px;
                border: none;
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
            }}
            QCheckBox::indicator:unchecked {{
                image: url("{assets}checkbox_unchecked.png");
            }}
            QCheckBox::indicator:checked {{
                image: url("{assets}checkbox_checked.png");
            }}
        """)

class ScrollableMessageBox(QDialog):
    def __init__(self, title, message, parent =None):
        super().__init__(parent)
        self.setWindowTitle(title)

        layout = QVBoxLayout(self)

        text_edit = QTextEdit(self)
        text_edit.setReadOnly(True)
        text_edit.setPlainText(message)
        layout.addWidget(text_edit)

        ok_button = QPushButton('Aceptar', self)
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

class SpinnerOverlay(QWidget):
    def __init__(self, parent = None, mensaje="Procesando..."):
        super().__init__(parent)

        # Ventana sin bordes, bloqueante y transparente
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120); border: none;")

        # Expandirse al tamaño del padre
        if parent:
            self.resize(parent.size())
            self.move(parent.pos())
        else:
            self.resize(300, 300)

        # Layout para centrar el spinner
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        # TEXTO
        self.label_texto = QLabel(mensaje, self)
        self.label_texto.setAlignment(Qt.AlignCenter)
        self.label_texto.setStyleSheet('''
                                    color: black;
                                    font-size: 12px;
                                    font-weight: bold;
                                    background: transparent;
                                    margin-bottom: 30px;
                                       ''')
        
        # GIF
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background: transparent; border: none;")

        self.movie = QMovie(SPINNER)
        self.label.setMovie(self.movie)
        self.movie.start()
        
        # Añadir al layout        
        layout.addWidget(self.label_texto)
        layout.addWidget(self.label)        

    def setMensaje(self, mensaje):
        # Permite cambiar el texto dinámicamente.
        self.label_texto.setText(mensaje)

'''
Esta clase crea un cuadro de diálogo con el que vamos a poder seleccionar
la carpeta de destino donde queremos mover los archivos elegidos.
Nos mostrará una lista de todos los directorios contenidos dentro del
directorio principal, con lo cual, no podremos mover archivos por
directorios que no correspondan a la aplicación.
Se hace una importación local para que no haya problemas importación
circular.
Para que no haya un error al mover el archivo a la misma carpeta desde la
que se quiere mover, no presentamos en el listado la ruta de origen (ruta_actual).
'''
class SelectorCarpeta(QDialog):
    def __init__(self, ruta_actual, parent = None):
        from main import MapaWindow # Evita importación circular.

        super().__init__(parent)
        self.setWindowTitle("Seleccionar la carpeta de destino")

        layout = QVBoxLayout(self)

        # Lista con las carpetas del directorio principal.
        '''
        Lista todas las carpetas del directorio menos la que coincide
        con la ruta de origen de la foto que queremos mover, ya que 
        daría error, y donde están los archivos que no han sido clasificados
        y están pendiente de ellos (Sin_GPS).
        '''
        self.list = QListWidget()
        mensaje = ''
        for f in os.scandir(RUTA_PRINCIPAL):
            if f.is_dir():
                if ruta_actual == f"{RUTA_PRINCIPAL}\\{f.name}" or f.name == '(Sin_GPS)': # Comprobar ruta actual.
                    continue
                self.list.addItem(f.name)
                mensaje += f'{f.name}\n' # str con todas las carpetas.

        # Ajustamos el tamaño del QDialog a los datos obtenidos.
        ancho, alto = MapaWindow.analizar_mensaje(mensaje)
        ancho = min(500, 7 * ancho)
        alto = min(600, 25 * alto)
        self.resize(ancho, alto) # Ajustamos el tamaño del QDialog.

        layout.addWidget(self.list)

        # Layout conjunto botones añadir y aceptar.
        layout_btn = QHBoxLayout()
        layout_btn.addStretch()

        # Botón añadir carpeta.
        self.btn_anadir = QPushButton("➕ Añadir", self)
        self.btn_anadir.clicked.connect(self._abrir_dialogo_crear_carpeta)
        layout_btn.addWidget(self.btn_anadir)

        # Botón aceptar.
        self.btn_aceptar = QPushButton("Aceptar", self)
        self.btn_aceptar.setEnabled(False) # Botón deshabilitado.
        self.btn_aceptar.clicked.connect(self.accept)
        layout_btn.addWidget(self.btn_aceptar)

        layout.addLayout(layout_btn)

        # Habilitar el botón cuando se seleccione algo.
        # Señal que se emite cada vez que cambia la selección.
        self.list.itemSelectionChanged.connect(self._habilitar_boton)

    '''
    Función para habilitar si se selecciona una opción de la lista.
    'currentItem()' devuelve None si no hay nada seleccionado, y
    con ese valor habilitamos o no el botón.
    '''
    def _habilitar_boton(self):
        self.btn_aceptar.setEnabled(self.list.currentItem() is not None)

    # Función donde obtenemos la ruta completa elegida.
    # A esta función la llamamos desde la función del Bridge 'mover'.
    def carpeta_seleccionada(self):
        item = self.list.currentItem()
        if item:
            ruta = os.path.join(RUTA_PRINCIPAL, item.text())
            return ruta
        
    def _abrir_dialogo_crear_carpeta(self):
        from componentes.dialogo_crear_carpeta import DialogoCrearCarpeta

        dlg = DialogoCrearCarpeta(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        
        ciudad, pais, fecha = dlg.resultado
        nombre_carpeta = f"({ciudad})({pais})({fecha})"
        ruta = os.path.join(RUTA_PRINCIPAL, nombre_carpeta)

        # Crear carpeta si no existe.
        if not os.path.exists(ruta):
            os.makedirs(ruta)

        # Añadir a la lista.
        self.list.addItem(nombre_carpeta)

        # Seleccionarla automáticamente.
        items = self.list.findItems(nombre_carpeta, Qt.MatchExactly)
        if items:
            self.list.setCurrentItem(items[0])
            