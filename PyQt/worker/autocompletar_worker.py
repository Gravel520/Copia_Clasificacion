'''
Script en Python.
'''

import time

from PyQt5.QtCore import QThread, pyqtSignal

from utils.utils_cache import cargar_cache, guardar_cache
from utils.utils_provincias import completar_datos_registro

class AutocompletarWorker(QThread):
    progreso = pyqtSignal(int)
    mensaje = pyqtSignal(str)
    terminado = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.cancelado = False

    def cancelar(self):
        self.cancelado = True

    def run(self):
        data = cargar_cache()
        total = len(data)

        cambios = False

        for indice, (clave, info) in enumerate(data.items(), start=1):
            if self.cancelado:
                return
            
            postal = str(info.get("postal", ""))

            necesita_autocompletar = (
                not info.get("ciudad")
                or not info.get("provincia")
                or not postal
            )

            if necesita_autocompletar:
                self.mensaje.emit(
                    (
                        f"{indice}/{total}\n"
                        f"{clave}"
                    )
                )

                try:
                    if completar_datos_registro(info):
                        cambios = True

                except Exception as e:
                    print(f"[ERROR] {clave}: {e}")
                time.sleep(1)

            self.progreso.emit(indice)

        if cambios:
            guardar_cache(data)

        self.terminado.emit(data)
