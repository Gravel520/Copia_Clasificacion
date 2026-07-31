'''
Script en Python.

Esto detecta:
    Imágenes que no pueden abrirse.
    Vídeos que no pueden analizarse.
    Archivos con firmas internas incorrectas.
'''

import os
import subprocess

from PIL import Image
from pathlib import Path

from config_paths import extensiones_validas

FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"

def check_archivos_corruptos(data_json):
    problemas = []

    try:
        clasificados = data_json.get("clasificados", {}).get("items", [])

        for item in clasificados:
            ruta = item.get("ruta")
            ubicacion = item.get("ubicacion")
            fecha = item.get("fecha")        
            if not ruta:
                continue

            ruta = Path(ruta).resolve()

            if not ruta.exists():
                continue

            ext = ruta.suffix.lower()

            # VALIDAR IMÁGENES
            if ext in extensiones_validas("imagen"):
                try:
                    with Image.open(ruta) as img:
                        img.verify()
                except Exception:
                    problemas.append({
                    "tipo": "imagen_corrupta",
                    "ruta": ruta,
                    "ubicacion": ubicacion + fecha,
                    "detalle": ubicacion + fecha,
                    "mensaje": "No se pudo abrir la imagen"
                    })
            
            # VALIDAR VÍDEOS
            elif ext in extensiones_validas("video"):
                cmd = (
                    f'"{FFPROBE}" '
                    f'-v error '
                    f'-select_streams v:0 '
                    f'-show_entries stream=codec_name '
                    f'-of default=noprint_wrappers=1:nokey=1 '
                    f'"{ruta}"'
                )
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, 
                    text=True
                )

                # ffprobe devuelve error real  si video corrupto
                if result.returncode != 0:
                    problemas.append({
                    "tipo": "video_corrupto",
                    "ruta": str(ruta),
                    "ubicacion": ubicacion + fecha,
                    "detalle": ubicacion + fecha,
                    "mensaje": "No se pudo abrir el video"
                    })
                    continue

                # ffprobe no encontró stream de video corrupto
                if not result.stdout.strip():
                    problemas.append({
                    "tipo": "video_corrupto",
                    "ruta": str(ruta),
                    "ubicacion": ubicacion + fecha,
                    "detalle": ubicacion + fecha,
                    "mensaje": "No se pudo abrir el video"
                    })

        return {
            "nombre": "Archivos corruptos",
            "problemas": problemas
        }
    
    except Exception as e:
        return {
            "nombre": "error",
            "problemas": [{
                "tipo": "Archivos corruptos",
                "ruta": "",
                "ubicacion": "",
                "detalle": str(e),
                "mensaje": "Error al comprobar archivos corruptos"
            }]
        }
    