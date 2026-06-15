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

def run_autodiagnostico(ruta_json_unico, raiz_backup, chequeos):
    """
    chequeos: lista de strings:
      ["completo"] o combinación de:
      "json_carpetas", "json_cache", "integridad", "directorios", "corrupcion"
    """

    data = cargar_json_unico(ruta_json_unico)
    cache = cargar_cache()

    resultados = []

    def ejecutar_completo():
        res = []
        res.append(check_json_vs_carpetas(data, raiz_backup))
        res.append(check_json_vs_cache(data, cache))
        res.append(check_integridad_archivos(data))
        res.append(check_directorios_vacios(raiz_backup))
        res.append(check_archivos_corruptos(data))
        return res
    
    if "completo" in chequeos:
        resultados.extend(ejecutar_completo())
        return resultados
    
    if "json_carpetas" in chequeos:
        resultados.append(check_json_vs_carpetas(data, raiz_backup))
    
    if "json_cache" in chequeos:
        resultados.append(check_json_vs_cache(data, cache)) 

    if "integridad" in chequeos:
        resultados.append(check_integridad_archivos(data))

    if "directorios" in chequeos:
        resultados.append(check_directorios_vacios(raiz_backup)) 

    if "corrupcion" in chequeos:
        resultados.append(check_archivos_corruptos(data)) 

    return resultados
