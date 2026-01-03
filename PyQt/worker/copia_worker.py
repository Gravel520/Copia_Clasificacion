'''

'''

from PyQt5.QtCore import QThread, pyqtSignal
from copia_clasificador_fotos import (
    obtener_archivos,
    clasificar_archivo,
    cargar_json_unico,
    actualizar_stats,
    guardar_json_unico,
    borrar_directorios_vacios,
    RUTA_JSON_UNICO,
    RUTA_TEMPORAL,
    RUTA_MOVIL
)
import os
import shutil
from config import NUMERO_FOTO_INICIO, CANTIDAD_FOTOS_A_CLASIFICAR

class CopiaWorker(QThread):
    terminado = pyqtSignal(str)     # Mensaje final
    progreso = pyqtSignal(int)      # Archivos procesados
    total = pyqtSignal(int)         # Total de archivos

    def __init__(self, carpeta_origen=None):
        super().__init__()
        self.carpeta_origen = carpeta_origen

    def run(self):
        # Estas líneas son para depurar dentro de los hilos.
        try:
            #import debugpy
            #debugpy.debug_this_thread()

            # 1️⃣ Obtener lista de archivos antes de clasificar
            archivos = obtener_archivos(self.carpeta_origen)
            archivos = archivos[NUMERO_FOTO_INICIO:(NUMERO_FOTO_INICIO + CANTIDAD_FOTOS_A_CLASIFICAR)]

            archivos = [
                a for a in archivos
                if a.lower().endswith(('.jpg', '.jpeg', '.mp4'))
            ]

            total = len(archivos)
            self.total.emit(total)

            if total == 0:
                self.terminado.emit("No hay archivos para clasificar.")
                return

            # 2️⃣ preparar el entorno.
            os.makedirs(RUTA_TEMPORAL, exist_ok=True)
            data = cargar_json_unico(RUTA_JSON_UNICO)
            ruta_archivos = self.carpeta_origen if self.carpeta_origen else RUTA_MOVIL

            # 3️⃣ Clasificar uno por uno
            procesados = 0
            mensaje = ""            

            for archivo in archivos:
                mensaje += clasificar_archivo(archivo, ruta_archivos, data)
                procesados += 1
                self.progreso.emit(procesados)

            # 4️⃣ Guardar cambios.
            actualizar_stats(data)
            guardar_json_unico(RUTA_JSON_UNICO, data)

            shutil.rmtree(RUTA_TEMPORAL)
            borrar_directorios_vacios()

            self.terminado.emit(mensaje)

        except Exception as e:
            self.terminado.emit(f"Error: {e}")
