'''

'''

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton,
    QPushButton
)
from PyQt5.QtCore import Qt
from componentes.range_slider import QRangeSlider

class DialogoSeleccionCantidad(QDialog):
    def __init__(self, total_archivos, parent =None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar cantidad a clasificar")
        self.setGeometry(400, 300, 300, 180)        
        self.total = total_archivos

        layout = QVBoxLayout(self)

        # Texto informativo
        layout.addWidget(QLabel(f'Total de archivos encontrados: {total_archivos}'))

        # Opciones
        self.radio_todos = QRadioButton("Clasificar todos")
        self.radio_intervalo = QRadioButton("Clasificar intervalo")
        self.radio_todos.setChecked(True)        

        self.radio_todos.toggled.connect(self.modo_cambiado)
        self.radio_intervalo.toggled.connect(self.modo_cambiado)

        layout.addWidget(self.radio_todos)
        layout.addWidget(self.radio_intervalo)

        # Slider doble
        self.slider = QRangeSlider()
        self.slider.setRange(0, total_archivos)
        self.slider.setValues(0, total_archivos)

        self.label_intervalo = QLabel(f"Intervalo: 0 - {total_archivos}         Cantidad: {total_archivos}")
        self.slider.valueChanged.connect(self.actualizar_intervalo)
        self.slider.setEnabled(False)

        layout.addWidget(self.label_intervalo)
        layout.addWidget(self.slider)

        # Botones
        botones = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)

        layout.addLayout(botones)

    def modo_cambiado(self):
        if self.radio_todos.isChecked():
            # Rango completo
            self.slider.setValues(0, self.total)
            self.label_intervalo.setText(f"Intervalo: 0 - {self.total}         Cantidad: {self.total}")

            # Desactivar slider
            self.slider.setEnabled(False)
        else:
            # Activar slider
            self.slider.setEnabled(True)

    def actualizar_intervalo(self, inicio, fin):
        self.label_intervalo.setText(f"Intervalo: {inicio} - {fin}          Cantidad: {int(fin - inicio)}")

    def obtener_resultado(self):
        if self.radio_todos.isChecked():
            return {
                "modo": "todos",
                "inicio": 0,
                "fin": self.total
            }
        else:
            inicio, fin = self.slider._start, self.slider._end
            return {
                "modo": "intervalo",
                "inicio": inicio,
                "fin": fin
            }
        