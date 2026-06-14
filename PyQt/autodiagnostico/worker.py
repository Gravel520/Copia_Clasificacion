'''
Scrip en Python.
'''

from PyQt5.QtCore import QObject, pyqtSignal
from .motor import run_autodiagnostico

class WorkerAutodiagnostico(QObject):
    progreso = pyqtSignal(str) # Mensaje de estado
    terminado = pyqtSignal(list) # Resultado final

    def __init__(self, ruta_json, raiz_backup, modo="completo"):
        super().__init__()
        self.ruta_json = ruta_json
        self.raiz_backup = raiz_backup
        self.modo = modo

    def run(self):
        self.progreso.emit("Iniciando autodiagnóstico...")

        reporte = run_autodiagnostico(
            self.ruta_json,
            self.raiz_backup,
            self.modo
        )

        self.progreso.emit("Autodiagnóstico completado.")
        self.terminado.emit(reporte)
