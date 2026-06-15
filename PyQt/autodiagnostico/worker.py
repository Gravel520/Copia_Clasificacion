'''
Scrip en Python.
'''

from PyQt5.QtCore import QObject, pyqtSignal
from .motor import run_autodiagnostico

class WorkerAutodiagnostico(QObject):
    progreso = pyqtSignal(str) # Mensaje de estado
    avance = pyqtSignal()
    terminado = pyqtSignal(list) # Resultado final

    def __init__(self, ruta_json, raiz_backup, chequeos):
        super().__init__()
        self.ruta_json = ruta_json
        self.raiz_backup = raiz_backup
        self.chequeos = chequeos

    def run(self):
        self.progreso.emit("Iniciando autodiagnóstico...")

        resultados = run_autodiagnostico(
            self.ruta_json,
            self.raiz_backup,
            self.chequeos
        )

        # Barra de progreso: tantos pasos como chequeos
        for _ in resultados:
            self.avance.emit()

        self.progreso.emit("Autodiagnóstico completado.")
        self.terminado.emit(resultados)
        