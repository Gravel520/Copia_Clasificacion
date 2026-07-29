'''

'''

from PyQt5.QtCore import QThread, pyqtSignal
from copia_clasificador_fotos import (
    obtener_archivos,
    clasificar_archivo,
    cargar_json_unico,
    actualizar_stats,
    guardar_json_unico,
    borrar_directorios_vacios
)
from config_paths import ruta_json_unico, get_ruta_temporal, ruta_movil, extensiones_validas
import os
import shutil

class CopiaWorker(QThread):
    terminado = pyqtSignal(str)     # Mensaje final
    progreso = pyqtSignal(str)      # Archivos procesados
    total = pyqtSignal(int)         # Total de archivos

    def __init__(self, carpeta_origen, modo="todos", inicio=0, fin=0):
        super().__init__()
        self.carpeta_origen = carpeta_origen
        self.modo = modo
        self.inicio = inicio
        self.fin = fin
        self.detener = False

    def run(self):
        # Estas líneas son para depurar dentro de los hilos.
        try:
            import debugpy
            debugpy.debug_this_thread()

            # 1️⃣ Obtener lista de archivos antes de clasificar
            archivos = obtener_archivos(self.carpeta_origen)
            if self.modo != "todos":
                archivos = archivos[self.inicio:self.fin]

            archivos = [
                a for a in archivos
                if a.lower().endswith(extensiones_validas())
            ]

            total = len(archivos)
            self.total.emit(total)

            if total == 0:
                self.terminado.emit("No hay archivos para clasificar.")
                return
            
            # Deteccion PC / Movil
            usar_movil = not self.es_ruta_de_pc(self.carpeta_origen)
            ruta_archivos = self.carpeta_origen if not usar_movil else ruta_movil()

            # 2️⃣ preparar el entorno.
            os.makedirs(get_ruta_temporal(), exist_ok=True)
            data = cargar_json_unico(ruta_json_unico())

            # 3️⃣ Clasificar uno por uno
            mensaje = ""            

            for archivo in archivos:
                if self.detener:
                    break

                tipo, msg = clasificar_archivo(archivo, ruta_archivos, data, usar_movil)
                mensaje += msg

                self.progreso.emit(tipo)

            # 4️⃣ Guardar cambios.
            actualizar_stats(data)
            guardar_json_unico(ruta_json_unico(), data)

            shutil.rmtree(get_ruta_temporal())
            borrar_directorios_vacios()

            self.terminado.emit(mensaje)

        except Exception as e:
            self.terminado.emit(f"Error: {e}")

    def es_ruta_de_pc(self, ruta):
        return ruta is not None and ruta != "" and os.path.exists(ruta)

    def stop_thread(self):
        self.detener = True
