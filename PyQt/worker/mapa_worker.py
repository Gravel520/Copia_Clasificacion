'''

'''

from PyQt5.QtCore import QThread, pyqtSignal
from mapa_generator import cargar_datos_desde_historial
from copia_clasificador_fotos import cargar_json_unico
from config_paths import ruta_json_unico

class MapaWorker(QThread):
    terminado = pyqtSignal()
    pendientes_actualizados = pyqtSignal(int)

    def run(self):
        cargar_datos_desde_historial()

        # Cargar JSON unificado
        data = cargar_json_unico(ruta_json_unico())
        total = len(data["pendientes"]["items"])

        # Emitir señal
        self.pendientes_actualizados.emit(total)

        self.terminado.emit()
        