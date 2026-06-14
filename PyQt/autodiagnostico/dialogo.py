'''
Script en Python.
'''

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton
)
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QThread

from .worker import WorkerAutodiagnostico

class DialogoAutodiagnostico(QDialog):
    def __init__(self, ruta_json, raiz_backup, modo="completo",parent = None):
        super().__init__(parent)
        self.setWindowTitle("Autodiagnóstico del sistema")
        self.resize(500, 400)

        layout = QVBoxLayout(self)

        # Spinner GIF
        self.lblSpinner = QLabel()
        self.movie = QMovie("assets/spinner.gif")
        self.lblSpinner.setMovie(self.movie)
        layout.addWidget(self.lblSpinner)

        # Mensaje de estado
        self.lblEstado = QLabel("Preparando...")
        layout.addWidget(self.lblEstado)

        # Área de reporte
        self.txtReporte = QTextEdit()
        self.txtReporte.setReadOnly(True)
        layout.addWidget(self.txtReporte)

        # Botón cerrar
        self.btnCerrar = QPushButton("Cerrar")
        self.btnCerrar.setEnabled(False)
        self.btnCerrar.clicked.connect(self.close)
        layout.addWidget(self.btnCerrar)

        # Crear hilo + worker
        self.thread = QThread()
        self.worker = WorkerAutodiagnostico(
            ruta_json, raiz_backup, modo
        )
        self.worker.moveToThread(self.thread)

        # Conexiones
        self.thread.started.connect(self.worker.run)
        self.worker.progreso.connect(self.actualizar_estado)
        self.worker.terminado.connect(self.finalizar)

        # Cuando termine, cerramos el hilo
        self.worker.terminado.connect(self.thread.quit)
        self.worker.terminado.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Iniciar
        self.movie.start()
        self.thread.start()

    def actualizar_estado(self, mensaje):
        self.lblEstado.setText(mensaje)

    def finalizar(self, reporte):
        self.movie.stop()
        self.lblSpinner.hide()

        texto = ""
        for bloque in reporte:
            texto += f"🔍 {bloque['chequeo']}\n"
            texto += f"Problemas detectados: {bloque['total_problemas']}\n"
            for p in bloque["detalle"]:
                texto += f" - {p}\n"
            texto += "\n"

        self.txtReporte.setText(texto)
        self.lblEstado.setText("Autodiagnóstico finalizado.")
        self.btnCerrar.setEnabled(True)
