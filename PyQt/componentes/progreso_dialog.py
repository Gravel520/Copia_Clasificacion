'''

'''

import time
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt

class ProgresoClasificacion(QDialog):
    def __init__(self, total_archivos, parent = None):
        super().__init__(parent)

        self.setWindowTitle("Clasificando archivos...")
        self.setModal(True)
        self.setFixedSize(400, 130)

        layout = QVBoxLayout(self)

        # Texto superior.
        self.label_info = QLabel(f"Archivos a clasificar: {total_archivos}")
        self.label_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_info)

        # Barra de progreso.
        self.barra = QProgressBar()
        self.barra.setRange(0, total_archivos)
        self.barra.setValue(0)
        layout.addWidget(self.barra)

        # Tiempo estimado.
        self.label_tiempo = QLabel("Tiempo estimado: calculando...")
        self.label_tiempo.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_tiempo)

        # Para calcular estimación.
        self.inicio = time.time()

    def actualizar(self, actual):
        self.barra.setValue(actual)

        # Calcular tiempo estimado.
        transcurrido = time.time() - self.inicio
        if actual > 0:
            estimado_total = transcurrido / actual * self.barra.maximum()
            restante = estimado_total - transcurrido
            self.label_tiempo.setText(
                f"Tiempo estimado restante: {int(restante)} s"
            )
