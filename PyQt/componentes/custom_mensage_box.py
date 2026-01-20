'''

'''

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt

class CustomMessageBox(QDialog):
    def __init__(self, titulo, mensaje, parent = None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        # Texto largo con scroll
        self.texto = QTextEdit(self)
        self.texto.setReadOnly(True)
        self.texto.setPlainText(mensaje)

        # Calcular altura según líneas
        lineas = mensaje.count("\n") + 1
        altura = min(600, 20 * lineas) # Máximo 600 px
        self.texto.setMidLineWidth(580)
        self.texto.setFixedHeight(altura)

        layout.addWidget(self.texto)

        # Botón cerrar
        btn = QPushButton("Cerrar")
        btn.clicked.connect(self.accept)

        botones = QHBoxLayout()
        botones.addStretch()
        botones.addWidget(btn)

        layout.addLayout(botones)
