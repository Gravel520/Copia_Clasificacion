'''
Script en Python.
'''

import os
import json
import shutil
import tempfile
import zipfile
import time

from PyQt5.QtCore import QObject, pyqtSignal

from utils.utils_biblioteca import copiar_carpeta_cancelable, formatear_segundos


class ExportadorBiblioteca(QObject):
    progreso_metadatos = pyqtSignal(int)
    progreso_miniaturas = pyqtSignal(int)
    progreso_fotos = pyqtSignal(int)
    progreso_compresion = pyqtSignal(int)

    archivo_actual = pyqtSignal(str)
    tiempo_restante = pyqtSignal(str)

    estado = pyqtSignal(str)
    finalizado = pyqtSignal(bool, str)

    # AÑADIR CONSTANTES DE VELOCIDAD
    VELOCIDAD_COPIA = 120 * 1024 * 1024    # 120 MB/s
    VELOCIDAD_ZIP = 35 * 1024 * 1024       # 35 MB/s
    FACTOR_SEGURIDAD = 1.5                 # Factor corrector

    def __init__(self, ruta_biblioteca, ruta_json, ruta_cache, ruta_grupos, ruta_miniaturas, destino_fbk):
        super().__init__()

        self.progreso_metadatos_actual = 0
        self.progreso_miniaturas_actual = 0
        self.progreso_fotos_actual = 0

        self.ruta_biblioteca = ruta_biblioteca
        self.ruta_json = ruta_json
        self.ruta_cache = ruta_cache
        self.ruta_grupos = ruta_grupos
        self.ruta_miniaturas = ruta_miniaturas
        self.destino_fbk = destino_fbk
        self.total_bytes_global = 0
        self.bytes_procesados_global = 0
        self.tiempo_total_estimado = 0

        self.cancelado = False

    def run(self):
        try:
            #self.inicio = time.time()
            self.bytes_procesados_global = 0

            self.tiempo_total_estimado = (
                self.calcular_estimacion_inicial()
            )

            self.inicio = time.time()

            self.tiempo_restante.emit(
                formatear_segundos(
                    self.tiempo_total_estimado
                )
            )

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

                self.progreso_metadatos.emit(100)

                self.progreso_metadatos_actual = 100

                self.total_miniaturas = sum(len(files) for _, _, files in os.walk(self.ruta_miniaturas))

                self.miniaturas_copiadas = 0

                miniaturas_dir = os.path.join(temp, "miniaturas")
                os.makedirs(miniaturas_dir, exist_ok=True)

                self.estado.emit("Copiando miniaturas...")

                copiar_carpeta_cancelable(self.ruta_miniaturas, miniaturas_dir, lambda: self.cancelado, self._miniatura_copiada)

                self.total_bytes = 0

                for root, _, files in os.walk(self.ruta_biblioteca):
                    for f in files:
                        self.total_bytes += os.path.getsize(os.path.join(root, f))

                self.bytes_copiados = 0

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

                    copiar_carpeta_cancelable(origen, destino, lambda: self.cancelado, self._foto_copiada)

                manifest = {
                    "version": "1.0",
                    "total_carpetas": len(carpetas),
                    "miniaturas": True
                }

                with open(os.path.join(metadata_dir, "manifest.json"), "w", encoding="utf-8") as f:
                    json.dump(manifest, f, indent=4, ensure_ascii=False)

                self.estado.emit("Comprimiendo biblioteca...")

                with zipfile.ZipFile(self.destino_fbk, "w", zipfile.ZIP_DEFLATED) as zipf:
                    archivos_zip = []

                    for root, _, files in os.walk(temp):
                        for file in files:
                            archivos_zip.append(os.path.join(root, file))

                    total_zip = len(archivos_zip)

                    for i, archivo in enumerate(archivos_zip):                        
                        arcname = os.path.relpath(archivo, temp)

                        self.archivo_actual.emit(os.path.basename(archivo))
                        self.estado.emit("Comprimiento biblioteca...")

                        if self.cancelado:
                            raise InterruptedError("CANCELADO")
                        
                        zipf.write(archivo, arcname)

                        porcentaje = int((i + 1) * 100 / total_zip)

                        self.progreso_compresion.emit(porcentaje)
                        self.actualizar_tiempo_restante()
                        
                self.tiempo_restante.emit("00:00")
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

    def _miniatura_copiada(self, ruta):
        self.miniaturas_copiadas += 1

        porcentaje = int(self.miniaturas_copiadas * 100 / self.total_miniaturas)

        self.progreso_miniaturas_actual = (porcentaje)

        self.progreso_miniaturas.emit(porcentaje)
        self.actualizar_tiempo_restante()

    def _foto_copiada(self, ruta):
        if not os.path.exists(ruta):
            return
        
        tam = os.path.getsize(ruta)

        self.bytes_copiados += tam

        porcentaje = int(self.bytes_copiados * 100 / self.total_bytes)

        self.progreso_fotos.emit(porcentaje)

        self.archivo_actual.emit(os.path.basename(ruta))
        self.actualizar_tiempo_restante()

    def calcular_tamano_carpeta(self, ruta):
        total = 0

        if not os.path.exists(ruta):
            return 0
        
        for root, _, files in os.walk(ruta):
            for fichero in files:
                try:
                    total += os.path.getsize(os.path.join(root, fichero))

                except:
                    pass
        
        return total
    
    def calcular_estimacion_inicial(self):
        self.estado.emit("Analizando biblioteca...")

        bytes_metadatos = 0

        for fichero in (self.ruta_json, self.ruta_cache, self.ruta_grupos):
            if os.path.exists(fichero):
                bytes_metadatos += os.path.getsize(fichero)

        bytes_miniaturas = self.calcular_tamano_carpeta(self.ruta_miniaturas)

        bytes_fotos = self.calcular_tamano_carpeta(self.ruta_biblioteca)

        bytes_totales = (bytes_metadatos + bytes_miniaturas + bytes_fotos)

        tiempo_copia = (bytes_totales / self.VELOCIDAD_COPIA)

        tiempo_zip = (bytes_totales / self.VELOCIDAD_ZIP)

        return (tiempo_copia + tiempo_zip) * self.FACTOR_SEGURIDAD
    
    def actualizar_tiempo_restante(self):
        transcurrido = (
            time.time() - self.inicio
        )

        restante = (
            self.tiempo_total_estimado
            - transcurrido
        )

        self.tiempo_restante.emit(
            formatear_segundos(restante)
        )
    
    def cancelar(self):
        self.cancelado = True
