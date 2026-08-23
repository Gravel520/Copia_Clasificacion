'''
Script en Python.
'''

import os

from autodiagnostico.chequeos.json_vs_carpetas import construir_nombre_carpeta
from autodiagnostico.utils.deshabilitar_mapa import set_deshabilitar_mapa

from copia_clasificador_fotos import calcular_hash_md5, actualizar_stats

from config_paths import get_ruta_principal

def buscar_archivo_por_hash_en_carpeta(hash_buscado, ubicacion, fecha):
    carpeta = construir_nombre_carpeta(ubicacion, fecha)
    carpeta = os.path.join(get_ruta_principal(), carpeta)

    if not os.path.exists(carpeta):
        return None

    for archivo in os.listdir(carpeta):
        ruta_archivo = os.path.join(carpeta, archivo)

        if os.path.isfile(ruta_archivo) and calcular_hash_md5(ruta_archivo) == hash_buscado:
            return ruta_archivo

    return None

def corregir_ruta_vacia(lista_problemas, data):
    clasificados = data["clasificados"]["items"]

    for p in lista_problemas:
        hash_buscado = p.get("hash")
        ubicacion = p.get("ubicacion")
        fecha = p.get("fecha")

        ruta = buscar_archivo_por_hash_en_carpeta(hash_buscado, ubicacion, fecha)

        if ruta:
            entrada = next((x for x in clasificados if x["hash"] == hash_buscado), None)
            if entrada:
                entrada["ruta"] = ruta

    actualizar_stats(data)

    set_deshabilitar_mapa()
    return data
