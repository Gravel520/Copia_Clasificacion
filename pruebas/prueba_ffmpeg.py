import subprocess
import os
from pathlib import Path

FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"

ruta_origen = Path(r"C:\Movil_Jesus_A33\WhatsApp Video")
ruta_destino = Path(r"C:\Users\katal\Documents\Python\Copia_Clasificacion\pruebas")
ruta_marca = Path(r"C:\Users\katal\Documents\Python\Copia_Clasificacion\PyQt\assets")

archivos = os.listdir(ruta_origen)

for archivo in archivos[1:25]:
    archivo_video = ruta_origen / archivo
    miniatura = ruta_destino / f"{archivo}.jpg"
    marca = ruta_marca / "marca_video.png"

    try:
        subprocess.run([
            FFMPEG,
            "-y",
            "-i", str(archivo_video),
            "-ss", "00:00:05",
            "-vframes", "1",
            str(miniatura)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        miniatura_con_marca = ruta_destino / f"{archivo}_marca.jpg"

        subprocess.run([
            FFMPEG, "-y",
            "-i", str(miniatura),
            "-i", str(marca),
            "-filter_complex",
            # Escalar marca al 20% del ancho de la imagen
            "[1:v]scale=iw*0.4:-1[wm];"
            # Colocar marca en el centro
            "[0:v][wm]overlay=(W-w)/2:(H-h)/2",
            str(miniatura_con_marca)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    except Exception as e:
        print(f"Error generando miniatura: {e}")
