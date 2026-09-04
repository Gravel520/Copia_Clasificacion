'''
Script en Python.
'''

import os

from autodiagnostico.utils.deshabilitar_mapa import set_deshabilitar_mapa
from copia_clasificador_fotos import (
    agrupar_fecha_archivo, calcular_hash_md5, cargar_cache,
    actualizar_stats
)
from config_paths import get_ruta_principal

def reconstruir_archivo_huerfano(ruta_archivo, data):
    ruta_archivo_completa = os.path.join(get_ruta_principal(), ruta_archivo)

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

    # Si el archivo No existe usar valores por defecto.
    if not os.path.exists(ruta_archivo_completa):
        hash = "hash_huerfano"
        fecha_completa = fecha_str
        timestamp = 0
        lat, lon = 0, 0
    else:
        # Calcular hash
        hash = calcular_hash_md5(ruta_archivo_completa)

        # Obtener fecha completa, hora y timestamp desde el archivo
        fecha_completa, timestamp, hora = agrupar_fecha_archivo(ruta_archivo_completa, None)

        # Obtener coordenadas desde cache
        cache = cargar_cache()
        if ubicacion in cache:
            lat = cache[ubicacion]["lat"]
            lon = cache[ubicacion]["lon"]
        else:
            lat, lon = 0, 0

    data["clasificados"]["items"].append({
        "hash": hash,
        "ruta": ruta_archivo_completa,
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

    actualizar_stats(data)

    set_deshabilitar_mapa()
    return data
