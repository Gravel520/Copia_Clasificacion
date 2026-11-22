'''
Script en Python.
'''

import os
import json
import shutil
import tempfile
import zipfile

from PyQt5.QtCore import QObject, pyqtSignal

from utils.copia_cancelable import copiar_carpeta_cancelable


class ExportadorBiblioteca(QObject):
    progreso = pyqtSignal(int)
    estado = pyqtSignal(str)
    finalizado = pyqtSignal(bool, str)

    def __init__(self, ruta_biblioteca, ruta_json, ruta_cache, ruta_grupos, ruta_miniaturas, destino_fbk):
        super().__init__()

        self.ruta_biblioteca = ruta_biblioteca
        self.ruta_json = ruta_json
        self.ruta_cache = ruta_cache
        self.ruta_grupos = ruta_grupos
        self.ruta_miniaturas = ruta_miniaturas
        self.destino_fbk = destino_fbk

        self.cancelado = False

    def run(self):
        try:
            with tempfile.TemporaryDirectory() as temp:
                self.estado.emit("Preparando exportación...")

                metadata_dir = os.path.join(temp, "metadata")
                fotos_dir = os.path.join(temp, "fotos")

                os.makedirs(metadata_dir)
                os.makedirs(fotos_dir)

                self.estado.emit("Copiando metadatos...")

                shutil.copy2(
                    self.ruta_json,
                    os.path.join(metadata_dir, "archivos_unificados.json")
                )

                if os.path.exists(self.ruta_cache):
                    shutil.copy2(
                        self.ruta_cache, os.path.join(metadata_dir, "cache_geocoding.json")
                    )

                if os.path.exists(self.ruta_grupos):
                    shutil.copy2(
                        self.ruta_grupos, os.path.join(metadata_dir, "grupos.json")
                    )

                miniaturas_dir = os.path.join(temp, "miniaturas")
                os.makedirs(miniaturas_dir, exist_ok=True)

                self.estado.emit("Copiando miniaturas...")

                copiar_carpeta_cancelable(self.ruta_miniaturas, miniaturas_dir, lambda: self.cancelado)

                carpetas = [d for d in os.listdir(self.ruta_biblioteca)
                            if os.path.isdir(os.path.join(self.ruta_biblioteca, d))
                            ]
                total = max(len(carpetas), 1)

                for i, carpeta in enumerate(carpetas):
                    self.estado.emit(f"Copiando carpeta {i +1}/{total}")

                    if self.cancelado:
                        raise InterruptedError("CANCELADO")
                    
                    origen = os.path.join(self.ruta_biblioteca, carpeta)
                    destino = os.path.join(fotos_dir, carpeta)

                    copiar_carpeta_cancelable(origen, destino, lambda: self.cancelado)

                    self.progreso.emit(int((i + 1) * 50 / total))

                    manifest = {
                        "version": "1.0",
                        "total_carpetas": len(carpetas),
                        "miniaturas": True
                    }

                with open(os.path.join(metadata_dir, "manifest.json"), "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=4, ensure_ascii=False)

                self.progreso.emit(80)

                self.estado.emit("Comprimiendo biblioteca...")

                with zipfile.ZipFile(self.destino_fbk, "w", zipfile.ZIP_DEFLATED) as zipf:
                    archivos_zip = []

                    for root, _, files in os.walk(temp):
                        for file in files:
                            archivos_zip.append(os.path.join(root, file))

                    total_zip = len(archivos_zip)

                    for i, archivo in enumerate(archivos_zip):                        
                        arcname = os.path.relpath(archivo, temp)

                        if self.cancelado:
                            raise InterruptedError("CANCELADO")
                        
                        zipf.write(archivo, arcname)

                        self.progreso.emit(80 + int((i + 1) / total_zip * 20))
                        
                self.finalizado.emit(True, self.destino_fbk)
                self.estado.emit("Exportación completada.")

        except InterruptedError:
            if os.path.exists(self.destino_fbk):
                try:
                    os.remove(self.destino_fbk)
                except:
                    pass

            self.estado.emit("Exportación cancelada.")

            self.finalizado.emit(False, "CANCELADO")

        except Exception as e:
            self.finalizado.emit(False, str(e))

    def cancelar(self):
        self.cancelado = True
