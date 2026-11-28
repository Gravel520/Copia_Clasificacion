'''
Script en Python.
'''

import os
import shutil
import tempfile
import zipfile
import time

from PyQt5.QtCore import QObject, pyqtSignal

from utils.utils_biblioteca import copiar_carpeta_cancelable, formatear_segundos

class ImportadorBiblioteca(QObject):
    progreso_descompresion = pyqtSignal(int)
    progreso_fotos = pyqtSignal(int)
    progreso_metadatos = pyqtSignal(int)
    progreso_miniaturas = pyqtSignal(int)

    estado = pyqtSignal(str)
    finalizado = pyqtSignal(bool, str)

    archivo_actual = pyqtSignal(str)
    tiempo_restante = pyqtSignal(str)

    # Constantes de velocidad
    VELOCIDAD_DESCOMPRENSION = 50 * 1024 * 1024
    VELOCIDAD_COPIA = 120 * 1024 * 1024

    FACTOR_SEGURIDAD = 1.4

    def __init__(self, ruta_biblioteca, ruta_json, ruta_cache, ruta_grupos, ruta_miniaturas, archivo_fbk):
        super().__init__()

        self.ruta_biblioteca = ruta_biblioteca
        self.ruta_json = ruta_json
        self.ruta_cache = ruta_cache
        self.ruta_grupos = ruta_grupos
        self.ruta_miniaturas = ruta_miniaturas
        self.archivo_fbk = archivo_fbk

        self.tiempo_total_estimado = 0
        self.inicio = None

        self.cancelado = False
        self.carpetas_importadas = []

        self.total_fotos = 0
        self.fotos_importadas = 0

        self.total_miniaturas = 0
        self.miniaturas_importadas = 0

    def run(self):
        try:
            self.estado.emit("Analizando copia de seguridad...")

            self.tiempo_total_estimado = (self.calcular_estimacion_inicial())

            self.inicio = time.time()

            self.tiempo_restante.emit(formatear_segundos(self.tiempo_total_estimado))

            with tempfile.TemporaryDirectory() as temp:
                self.estado.emit("Descomprimiendo archivo...")
                
                with zipfile.ZipFile(self.archivo_fbk, "r") as zipf:
                    miembros = zipf.infolist()
                    total_zip = max(len(miembros), 1)

                    for i, miembro in enumerate(miembros):
                        if self.cancelado:
                            raise InterruptedError("CANCELADO")
                        
                        zipf.extract(miembro, temp)

                        self.archivo_actual.emit(os.path.basename(miembro.filename))

                        porcentaje = int((i + 1) * 100 / total_zip)

                        self.progreso_descompresion.emit(porcentaje)
                        print("ZIP: ", porcentaje)

                        self.actualizar_tiempo_restante()

                fotos_dir = os.path.join(temp, "fotos")

                self.total_fotos = sum(
                    len(files)
                    for _, _, files
                    in os.walk(fotos_dir)
                )

                self.fotos_importadas = 0
                
                carpetas = [
                    d for d
                    in os.listdir(fotos_dir)

                    if os.path.isdir(
                        os.path.join(
                            fotos_dir, d
                        )
                    )
                ]

                total_carpetas = max(len(carpetas), 1)

                for i, carpeta in enumerate(carpetas):
                    if self.cancelado:
                        raise InterruptedError("CANCELADO")
                    
                    self.estado.emit(f"Importando carpeta {i + 1}/{total_carpetas}")
                    
                    origen = os.path.join(fotos_dir, carpeta)
                    destino = os.path.join(self.ruta_biblioteca, carpeta)

                    if os.path.exists(destino):
                        shutil.rmtree(destino)

                    copiar_carpeta_cancelable(
                        origen,
                        destino,
                        lambda: self.cancelado,
                        self._foto_importada
                    )

                    self.carpetas_importadas.append(destino)

                self.estado.emit("Restaurando miniaturas...")

                miniaturas_origen = os.path.join(temp, "miniaturas")

                self.total_miniaturas = sum(
                    len(files)
                    for _, _, files
                    in os.walk(miniaturas_origen)
                )

                self.miniaturas_importadas = 0

                if os.path.exists(self.ruta_miniaturas):
                    shutil.rmtree(self.ruta_miniaturas)

                os.makedirs(self.ruta_miniaturas, exist_ok=True)

                copiar_carpeta_cancelable(
                    miniaturas_origen,
                    self.ruta_miniaturas,
                    lambda: self.cancelado,
                    self._miniatura_importada
                )                    

                self.estado.emit("Restaurando metadatos...")

                metadata = os.path.join(temp, "metadata")

                shutil.copy2(os.path.join(metadata, "archivos_unificados.json"), self.ruta_json)

                self.progreso_metadatos.emit(33)

                cache = os.path.join(metadata, "cache_geocoding.json")

                if os.path.exists(cache):
                    shutil.copy2(cache, self.ruta_cache)

                self.progreso_metadatos.emit(66)

                grupos = os.path.join(metadata, "grupos.json")

                if os.path.exists(grupos):
                    shutil.copy2(grupos, self.ruta_grupos)

                self.progreso_descompresion.emit(100)
                self.progreso_fotos.emit(100)
                self.progreso_metadatos.emit(100)
                self.progreso_miniaturas.emit(100)

                self.tiempo_restante.emit("00:00")

                self.estado.emit("Importación completada")                

                self.finalizado.emit(True, self.archivo_fbk)

        except InterruptedError:
            for carpeta in self.carpetas_importadas:
                try:
                    shutil.rmtree(carpeta)
                except:
                    pass

            self.estado.emit("Importación cancelada...")

            self.finalizado.emit(False, "CANCELADO")

        except Exception as e:
            self.finalizado.emit(False, f"Error: {e}")

    def calcular_estimacion_inicial(self):
        tam_fbk = os.path.getsize(self.archivo_fbk)

        tiempo_descomprension = (tam_fbk / self.VELOCIDAD_DESCOMPRENSION)

        tiempo_copia = (tam_fbk / self.VELOCIDAD_COPIA)

        return (tiempo_descomprension + tiempo_copia) * self.FACTOR_SEGURIDAD
        
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

    def _foto_importada(self, ruta):
        self.fotos_importadas += 1

        if self.total_fotos:
            porcentaje = int(self.fotos_importadas * 100 / self.total_fotos)

            self.progreso_fotos.emit(porcentaje)
            print("FOTOS: ", 
                  self.fotos_importadas,
                  self.total_fotos)

        self.archivo_actual.emit(os.path.basename(ruta))

        self.actualizar_tiempo_restante()

    def _miniatura_importada(self, ruta):
        self.miniaturas_importadas += 1
        
        if self.total_miniaturas:
            porcentaje = int(self.miniaturas_importadas * 100 / self.total_miniaturas)

            self.progreso_miniaturas.emit(porcentaje)
            print("MINIATURAS: ", 
                  self.miniaturas_importadas,
                  self.total_miniaturas)

        self.archivo_actual.emit(os.path.basename(ruta))

        self.actualizar_tiempo_restante()

    def cancelar(self):
        self.cancelado = True
