'''

'''

from PyQt5.QtCore import QThread, pyqtSignal
from mapa_generator import cargar_datos_desde_historial, cargar_json_unico
from config import RUTA_JSON_UNICO

class MapaWorker(QThread):
    terminado = pyqtSignal()
    pendientes_actualizados = pyqtSignal(int)

    def run(self):
        cargar_datos_desde_historial()

        # Cargar JSON unificado
        data = cargar_json_unico(RUTA_JSON_UNICO)
        total = len(data["pendientes"]["items"])

        # Emitir señal
        self.pendientes_actualizados.emit(total)

        self.terminado.emit()