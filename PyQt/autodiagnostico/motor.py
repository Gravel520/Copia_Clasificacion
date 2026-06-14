'''
Script en Python
'''

import os
import json

from copia_clasificador_fotos import (
    cargar_json_unico, cargar_cache
)

from .chequeos.json_vs_carpetas import check_json_vs_carpetas
from .chequeos.json_vs_cache import check_json_vs_cache
from .chequeos.integridad_archivos import check_integridad_archivos
from .chequeos.directorios_vacios import check_directorios_vacios
from .chequeos.corrupcion import check_archivos_corruptos

from .reporte import generar_reporte

def run_autodiagnostico(ruta_json_unico, raiz_backup, modo="completo"):
    """
    ruta_json_unico: ruta al JSON único.
    ruta_cache_ubicaciones: ruta al JSON del cache de geolocalización.
    raiz_backup: carpeta raíz donde están las carpetas tipo (ciudad)(pais)(fecha).
    modo: "rapido" o "completo".
    """

    data = cargar_json_unico(ruta_json_unico)
    cache = cargar_cache()

    resultados = []

    # Chequeos básicos
    resultados.append(check_json_vs_carpetas(data, raiz_backup))
    # Normalizar los nombres (Espana por España)
    resultados.append(check_json_vs_cache(data, cache)) 

    if modo == "completo":
        resultados.append(check_integridad_archivos(data)) 
        resultados.append(check_directorios_vacios(raiz_backup)) 
        resultados.append(check_archivos_corruptos(data)) 

    reporte = generar_reporte(resultados)
    return reporte
