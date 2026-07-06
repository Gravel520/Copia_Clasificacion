'''
Script en Python.
'''

import os

from copia_clasificador_fotos import (
    agrupar_fecha_archivo, calcular_hash_md5, cargar_cache
)
from config_paths import get_ruta_principal

def reconstruir_archivo_huerfano(ruta_archivo, data):
    ruta_archivo = os.path.join(get_ruta_principal(), ruta_archivo)

    archivo = os.path.basename(ruta_archivo)
    carpeta = os.path.basename(os.path.dirname(ruta_archivo))

    # Extraer parte de la carpeta
    partes = carpeta.split(")")
    partes = [p.replace("(", "") for p in partes if p]

    if len(partes) == 3:
        ubicacion, pais, fecha_str = partes

        ubicacion = f"({ubicacion})({pais})"
        fecha_str = f"({fecha_str})"

    else:
        ubicacion = "(Sin_GPS)(Sin_GPS)"
        fecha_str = "(0000-00)"

    # Calcular hash
    hash = calcular_hash_md5(ruta_archivo)

    # Obtener fecha completa, hora y timestamp desde el archivo
    fecha_completa, timestamp, hora = agrupar_fecha_archivo(ruta_archivo, None)

    # Obtener coordenadas desde cache
    cache = cargar_cache()
    if ubicacion in cache:
        lat = cache[ubicacion][0]
        lon = cache[ubicacion][1]
    else:
        lat, lon = 0, 0

    clasificados = data["clasificados"]["items"]

    clasificados.append({
        "hash": hash,
        "ruta": ruta_archivo,
        "ubicacion": ubicacion,
        "latitud": lat,
        "longitud": lon,
        "fecha": fecha_str,
        "fecha_completa": fecha_completa,
        "timestamp": timestamp
    })

    return data

def corregir_archivo_huerfano(lista_problemas, data):
    for p in lista_problemas:
        data = reconstruir_archivo_huerfano(p.get("ruta"), data)

    return data
