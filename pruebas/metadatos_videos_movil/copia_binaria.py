'''
Script en python.
Este código realiza un flujo completo de extracción forente y técnica:
primero extrae el archivo del movil de forma 'pura' y luego lee sus 
secretos internos.
La copia:
    Utiliza ADB en lugar del explorador normal de windows.
    pull -a: Es la clave. La opción -a le dice al movil; copia el
        archivo pero manten las fechas de creación y modificación 
        originales. No es un simple copiar/pegar, es una transferencia
        bit a bit.
    subprocess.run: Ejecuta el comando de consola directamente desde
        Python.

La extracción:
    Utiliza ExifTool, para utilizarlo hay que copiar tanto el archivo 
        exe, como la carpeta de files en el mismo lugar, y ejecutar
        ese comando, que es la herramienta más potente que existe
        para leer metadatos.
        Los parámetros que usa son estratégicos:
        - -json. Le pide a exiftool que entregue los datos en un 
            formato que Python entiende perfectamente (diccionarios).
        - -n. Convierte las coordenadas de "37 grados 48 ' a números
            decimales simples (37.8135), listos para usar en un mapa.
        - -ee. Fundamental para vídeo. Los móviles Android suelen esconder
            el GPS en pistas de datos ocultas dentro del MP4; sin esto,
            muchas veces el GPS daría vacío.
        -GPS... Le dices que solo te interesan esos tres datos para ir
            más rápido.

'''

import subprocess
ruta_adb = 'C:\\adb\\platform-tools\\adb.exe'
ruta_movil = '/sdcard/DCIM/Camera'

def copia_binaria_fuerza(archivo, ruta_local):
    ruta_origen = f"{ruta_movil}/{archivo}"
    print(ruta_origen)

    comando = f'{ruta_adb} pull -a "{ruta_origen}" "{ruta_local}"'

    try:
        subprocess.run(comando, shell=True)
        return True
    except:
        return False
import subprocess
import json
import os

# Define la ruta donde pusiste el exe
RUTA_EXIFTOOL = r'C:\exiftool\exiftool.exe' 

def obtener_metadatos_reales(ruta_archivo):
    # Verificamos si el archivo de video existe antes de llamar a exiftool
    if not os.path.exists(ruta_archivo):
        return f"Error: El archivo no existe en {ruta_archivo}"

    comando = [
        RUTA_EXIFTOOL, 
        '-json', 
        '-n',
        '-ee',           # Extraer metadatos embebidos (GPS en videos)
        '-GPSLatitude', 
        '-GPSLongitude', 
        '-CreateDate', 
        ruta_archivo
    ]

    try:
        proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        salida, _ = proceso.communicate()
        
        # --- DIAGNÓSTICO ---
        # Si la salida está vacía o no empieza por '[', no es un JSON válido
        texto_salida = salida.decode('utf-8', errors='ignore').strip()
        
        if not texto_salida:
            return "❌ ExifTool no devolvió nada. ¿La ruta del video es correcta?"
        
        if not texto_salida.startswith('['):
            return f"❌ ExifTool devolvió un error: {texto_salida}"
        # -------------------

        # ExifTool devuelve una lista de diccionarios
        datos = json.loads(salida)
        
        if datos:
            return datos[0] # Retornamos el primer (y único) elemento
        return {}

    except Exception as e:
        return f"Error al ejecutar ExifTool: {e}"


print(copia_binaria_fuerza("VID_20251024_205424.mp4", "C:\\FotosTemp"))

# Prueba con la ruta corregida
video_local = r"C:\FotosTemp\VID_20251024_205424.mp4"
meta = obtener_metadatos_reales(video_local)

print("*" * 30)
try:
    print(f"Latitud: {meta['GPSLatitude']}")
    print(f"Longitud: {meta['GPSLongitude']}")
    print(f"Fecha: {meta['CreateDate']}")
except:
    print(meta)
print("*" * 30)

    
