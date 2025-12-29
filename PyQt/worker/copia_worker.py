'''

'''

from PyQt5.QtCore import QThread, pyqtSignal
from copia_clasificador_fotos import main

class CopiaWorker(QThread):
    terminado = pyqtSignal(str) # Mensaje

    def __init__(self, carpeta_origen=None):
        super().__init__()
        self.carpeta_origen = carpeta_origen

    def run(self):
        # Estas líneas son para depurar dentro de los hilos.
        try:
            import debugpy
            debugpy.debug_this_thread()

            try:
                mensaje = main(self.carpeta_origen)
                self.terminado.emit(mensaje)
            except Exception as e:
                # Emitir también en caso de error para que el spinner se detenga.
                self.terminado.emit(f"Error al clasificar : {e}")
                
        except Exception as e:
            self.terminado.emit(f"Error en el debug : {e}")
