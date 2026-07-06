'''
Script en Python.
'''

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt5.QtCore import Qt

class WidgetError(QWidget):
    def __init__(self, titulo, detalle, callback_corregir=None, parent =None):
        super().__init__(parent)

        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 8px;
                background: #fafafa;
            }
            QLabel {
                font-size: 12px;
            }
            QLabel.titulo {
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 6px;
            }
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background: #ff0000;
                color: #fff;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #cc0000;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        lblTitulo = QLabel(titulo)
        lblTitulo.setObjectName("titulo")
        layout.addWidget(lblTitulo)

        lblDetalle = QLabel(detalle)
        lblDetalle.setWordWrap(True)
        layout.addWidget(lblDetalle)

        if callback_corregir:
            btnCorregir = QPushButton("Corregir")
            btnCorregir.clicked.connect(callback_corregir)
            layout.addWidget(btnCorregir, alignment=Qt.AlignRight)
            