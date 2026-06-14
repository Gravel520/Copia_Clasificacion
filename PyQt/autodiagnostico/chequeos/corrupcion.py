'''
Script en Python.

Esto detecta:
    Imágenes que no pueden abrirse.
    Vídeos que no pueden analizarse.
    Archivos con firmas internas incorrectas.
'''

import os
from PIL import Image
import subprocess

from config_paths import extensiones_validas

def check_archivos_corruptos(data_json):
    problemas = []

    clasificados = data_json.get("clasificados", {}).get("items", [])

    for item in clasificados:
        ruta = item.get("ruta")
        if not ruta or not os.path.exists(ruta):
            continue

        ext = ruta.lower().split(".")[-1]

        if ext in extensiones_validas("imagen"):
            try:
                with Image.open(ruta) as img:
                    img.verify()
            except Exception:
                problemas.append({
                "tipo": "imagen_corrupta",
                "ruta": ruta,
                })

        elif ext in extensiones_validas("video"):
            try:
                cmd = ["ffprobe", "-v", "error", "-show_format", ruta]
                subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            except Exception:
                problemas.append({
                "tipo": "video_corrupto",
                "ruta": ruta,
                })

    return {
        "nombre": "Archivos corruptos",
        "problemas": problemas
    }
