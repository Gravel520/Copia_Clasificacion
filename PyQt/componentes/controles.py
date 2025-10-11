'''
Script en Python. Contendrá los distintos componentes, controles o 
    widtget creados por nosotros y que vamos a acoplar a la ventana.

Button: QPushButton que forman cada uno de los dos botones que aparecen
    en la tabla de los listados de los archivos de imagen. Como parámetros
    recibe el nombre del icono, y el color del botón.
'''

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, QSize

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
