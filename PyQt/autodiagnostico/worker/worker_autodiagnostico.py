'''
Scrip en Python.
'''

from PyQt5.QtCore import QObject, pyqtSignal
from ..motor import (
    check_json_vs_carpetas,
    check_json_vs_cache,
    check_integridad_archivos,
    check_directorios_vacios,
    check_archivos_corruptos
)

class WorkerAutodiagnostico(QObject):
    progreso = pyqtSignal(str) # Mensaje de estado
    avance = pyqtSignal()
    estado_chequeo = pyqtSignal(str) # nombre del chequeo actual
    terminado = pyqtSignal(list) # Resultado final

    def __init__(self, ruta_json, raiz_backup, chequeos):
        super().__init__()
        self.ruta_json = ruta_json
        self.raiz_backup = raiz_backup
        self.chequeos = chequeos

    def run(self):
        resultados = []
        
        # Cargar datos una sola vez
        from ..motor import cargar_json_unico
        data = cargar_json_unico(self.ruta_json)

        # Lista de chequeos reales
        mapa = {
            "json_carpetas": check_json_vs_carpetas,
            "json_cache": check_json_vs_cache,
            "integridad": check_integridad_archivos,
            "directorios": check_directorios_vacios,
            "corrupcion": check_archivos_corruptos
        }

        # Si es completo -> reemplazar lista
        if "completo" in self.chequeos:
            self.chequeos = list(mapa.keys())

        # Ejecutar uno a uno
        for chk in self.chequeos:
            self.progreso.emit(f"Ejecutando chequeo {chk}...")
            self.estado_chequeo.emit(chk)

            funcion = mapa[chk]

            # Llamada correcta según parámetros
            if chk in ("json_carpetas",):
                resultado = funcion(data, self.raiz_backup)
            elif chk in ("json_cache",):
                from ..motor import cargar_cache
                cache = cargar_cache()
                resultado = funcion(data, cache)
            elif chk in ("integridad", "corrupcion"):
                resultado = funcion(data)
            elif chk in ("directorios",):
                resultado = funcion(self.raiz_backup)

            resultados.append(resultado)
            
            # Avanzar barra
            self.avance.emit()

        self.progreso.emit("Autodiagnóstico completado.")
        self.terminado.emit(resultados)
