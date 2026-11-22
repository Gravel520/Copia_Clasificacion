'''
Script en Python.
'''

import os
import shutil
import tempfile
import zipfile

from PyQt5.QtCore import QObject, pyqtSignal

from backup_completo.exportador_biblioteca import ExportadorBiblioteca

from utils.copia_cancelable import copiar_carpeta_cancelable

class ImportadorBiblioteca(QObject):
    progreso = pyqtSignal(int)
    estado = pyqtSignal(str)
    finalizado = pyqtSignal(bool, str)

    def __init__(self, ruta_biblioteca, ruta_json, ruta_cache, ruta_grupos, ruta_miniaturas, archivo_fbk):
        super().__init__()

        self.ruta_biblioteca = ruta_biblioteca
        self.ruta_json = ruta_json
        self.ruta_cache = ruta_cache
        self.ruta_grupos = ruta_grupos
        self.ruta_miniaturas = ruta_miniaturas
        self.archivo_fbk = archivo_fbk

        self.cancelado = False
        self.carpetas_importadas = []

    def run(self):
        try:
            with tempfile.TemporaryDirectory() as temp:
                self.estado.emit("Descomprimiendo archivo...")
                
                with zipfile.ZipFile(self.archivo_fbk, "r") as zipf:
                    zipf.extractall(temp)

                self.progreso.emit(20)

                fotos_dir = os.path.join(temp, "fotos")

                carpetas = [d for d in os.listdir(fotos_dir)
                            if os.path.isdir(os.path.join(fotos_dir, d))
                            ]
                
                total = max(len(carpetas), 1)

                for i, carpeta in enumerate(carpetas):
                    if self.cancelado:
                        raise InterruptedError()
                    
                    self.estado.emit(f"Importando carpeta {i + 1}/{total}")
                    
                    origen = os.path.join(fotos_dir, carpeta)
                    destino = os.path.join(self.ruta_biblioteca, carpeta)

                    if os.path.exists(destino):
                        shutil.rmtree(destino)

                    shutil.copytree(origen, destino)

                    self.carpetas_importadas.append(destino)

                    self.progreso.emit(20 + int((i + 1) / total * 60))

                self.estado.emit("Restaurando metadatos...")

                metadata = os.path.join(temp, "metadata")

                shutil.copy2(os.path.join(metadata, "archivos_unificados.json"), self.ruta_json)

                cache = os.path.join(metadata, "cache_geocoding.json")

                if os.path.exists(cache):
                    shutil.copy2(cache, self.ruta_cache)

                grupos = os.path.join(metadata, "grupos.json")

                if os.path.exists(grupos):
                    shutil.copy2(grupos, self.ruta_grupos)

                self.estado.emit("Restaurando miniaturas...")

                miniaturas_origen = os.path.join(temp, "miniaturas")

                if os.path.exists(self.ruta_miniaturas):
                    shutil.rmtree(self.ruta_miniaturas)

                os.makedirs(self.ruta_miniaturas, exist_ok=True)

                copiar_carpeta_cancelable(miniaturas_origen, self.ruta_miniaturas, lambda: self.cancelado)

                self.progreso.emit(100)

                self.finalizado.emit(True, self.archivo_fbk)

                self.estado.emit("Importación completada")

        except InterruptedError:
            for carpeta in self.carpetas_importadas:
                try:
                    shutil.rmtree(carpeta)
                except:
                    pass

            self.finalizado.emit(False, "Importación cancelada")

        except Exception as e:
            self.finalizado.emit(False, f"Error: {e}")
