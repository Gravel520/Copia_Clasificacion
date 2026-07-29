'''

'''

import time

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal

class ProgresoClasificacion(QDialog):
    cancelar = pyqtSignal() # Señal para cancelar el proceso

    def __init__(self, total_archivos, parent = None):
        super().__init__(parent)

        self.setWindowTitle("Clasificando archivos...")
        self.setModal(True)
        self.setFixedSize(500, 400)
        

        self.total_archivos = total_archivos
        self.procesados = 0
        self.clasificados = 0
        self.pendientes = 0
        self.eliminados = 0
        self.duplicados = 0

        # --- Estilo moderno para barras ---
        estilo_base = """
        QProgressBar {
            border: 1px solid #444;
            border-radius: 6px;
            background-color: #1e1e1e;
            height: 14px;
            text-align: center;
            color: white;
            font-size: 12px;
        }
        QProgressBar::chunk {
            border-radius: 6px;
        }
        """

        layout = QVBoxLayout(self)
        layout.setSpacing(25)
        layout.setContentsMargins(20, 20, 20, 20)

        # Zona superior (dashboard Header)
        zona_superior = QVBoxLayout()
        zona_superior.setSpacing(12)

        self.label_info = QLabel(f"Procesando archivo 0 de {total_archivos}")
        self.label_info.setAlignment(Qt.AlignCenter)
        self.label_info.setStyleSheet("font-size: 18px; font-weight: bold; color: black;")
        zona_superior.addWidget(self.label_info)

        # Barra de progreso.
        layout_total = QHBoxLayout()
        layout_total.setSpacing(12)

        label_total = QLabel("Total")
        label_total.setStyleSheet("color: #7D7777; font-size: 14px;")
        layout_total.addWidget(label_total)

        self.barra_total = QProgressBar()
        self.barra_total.setRange(0, total_archivos)
        self.barra_total.setValue(0)
        self.barra_total.setFormat("%p% del total")
        layout_total.addWidget(self.barra_total)

        zona_superior.addLayout(layout_total)
        layout.addLayout(zona_superior)

        # Zona central (dashboard Metrics)
        zona_barras = QVBoxLayout()
        zona_barras.setSpacing(18)

        def crear_bloque_barras(titulo, barra):
            bloque = QVBoxLayout()
            bloque.setSpacing(4)

            lbl = QLabel(titulo)
            lbl.setStyleSheet("color: #7D7777; font-size: 14px;")
            bloque.addWidget(lbl)

            bloque.addWidget(barra)

            return bloque
        
        # Clasificados
        self.barra_clasificados = QProgressBar()
        self.barra_clasificados.setRange(0, total_archivos)
        self.barra_clasificados.setFormat("%v clasificados")
        zona_barras.addLayout(crear_bloque_barras("Clasificados", self.barra_clasificados))

        # Pendientes
        self.barra_pendientes = QProgressBar()
        self.barra_pendientes.setRange(0, total_archivos)
        self.barra_pendientes.setFormat("%v pendientes")
        zona_barras.addLayout(crear_bloque_barras("Pendientes", self.barra_pendientes))

        # Eliminados
        self.barra_eliminados = QProgressBar()
        self.barra_eliminados.setRange(0, total_archivos)
        self.barra_eliminados.setFormat("%v eliminados")
        zona_barras.addLayout(crear_bloque_barras("Eliminados", self.barra_eliminados))

        # Duplicados
        self.barra_duplicados = QProgressBar()
        self.barra_duplicados.setRange(0, total_archivos)
        self.barra_duplicados.setFormat("%v duplicados")
        zona_barras.addLayout(crear_bloque_barras("Duplicados", self.barra_duplicados))

        layout.addLayout(zona_barras)

        self.barra_total.setStyleSheet(estilo_base + "QProgressBar::chunk { background-color: #3a8ee6; }")
        self.barra_clasificados.setStyleSheet(estilo_base + "QProgressBar::chunk { background-color: #4caf50; }")
        self.barra_pendientes.setStyleSheet(estilo_base + "QProgressBar::chunk { background-color: #ffc107; }")
        self.barra_eliminados.setStyleSheet(estilo_base + "QProgressBar::chunk { background-color: #f44336; }")
        self.barra_duplicados.setStyleSheet(estilo_base + "QProgressBar::chunk { background-color: #9c27b0; }")

        # Zona inferior (footer)
        zona_inferior = QVBoxLayout()
        zona_inferior.setSpacing(15)

        self.label_tiempo = QLabel("Tiempo estimado: calculando...")
        self.label_tiempo.setAlignment(Qt.AlignCenter)
        self.label_tiempo.setStyleSheet("color: #bbbbbb; font-size: 14px;")
        zona_inferior.addWidget(self.label_tiempo)

        boton_layout = QHBoxLayout()
        boton_layout.addStretch()
        
        # Botón cancelar        
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e46a67;
            }
        """)
        self.btn_cancelar.clicked.connect(self.cancelar.emit)

        boton_layout.addWidget(self.btn_cancelar)
        boton_layout.addStretch()

        zona_inferior.addLayout(boton_layout)
        layout.addLayout(zona_inferior)

        # Para calcular estimación.
        self.inicio = time.time()

    def actualizar(self, tipo_resultado):
        #self.barra.setValue(actual)
        '''
        tipo_resultado puede ser:
        'clasificado', 'pendiente', 'eliminado', 'duplicado'
        '''

        # Actualizar contadores
        self.procesados += 1
        self.barra_total.setValue(self.procesados)

        if tipo_resultado == 'clasificado':
            self.clasificados += 1
            self.barra_clasificados.setValue(self.clasificados)

        elif tipo_resultado == 'pendiente':
            self.pendientes += 1
            self.barra_pendientes.setValue(self.pendientes)

        elif tipo_resultado == 'eliminado':
            self.eliminados += 1
            self.barra_eliminados.setValue(self.eliminados)

        elif tipo_resultado == 'duplicado':
            self.duplicados += 1
            self.barra_duplicados.setValue(self.duplicados)

        # Texto superior
        self.label_info.setText(
            f"Procesando archivo {self.procesados} de {self.total_archivos}"
        )

        # Calcular tiempo estimado.
        transcurrido = time.time() - self.inicio
        if self.procesados > 0:
            estimado_total = transcurrido / self.procesados * self.total_archivos
            restante = estimado_total - transcurrido

            # Convertir a horas, minutos y segundos
            horas = int(restante // 3600)
            minutos = int(restante % 3600 // 60)
            segundos = int(restante % 60)

            cronometro = f'{horas:02d}:{minutos:02d}:{segundos:02d}'
            self.label_tiempo.setText(
                f"Tiempo estimado restante: {cronometro}"
            )
