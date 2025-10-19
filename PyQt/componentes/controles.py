'''
Script en Python. Contendrá los distintos componentes, controles o 
    widtget creados por nosotros y que vamos a acoplar a la ventana.

Button: QPushButton que forman cada uno de los dos botones que aparecen
    en la tabla de los listados de los archivos de imagen. Como parámetros
    recibe el nombre del icono, y el color del botón.
'''

from PyQt5.QtWidgets import QPushButton, QCheckBox, QMenu, QAction
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, QSize, pyqtSignal

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
