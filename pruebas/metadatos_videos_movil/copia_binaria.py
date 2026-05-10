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
from datetime import datetime
ruta_adb = 'C:\\adb\\platform-tools\\adb.exe'
ruta_movil = '/sdcard/DCIM/Camera'

def copia_binaria_fuerza(archivo, ruta_local):
    ruta_origen = f"{ruta_movil}/{archivo}"
    print(ruta_origen)

    if not os.path.exists(ruta_local):
        os.makedirs(ruta_local)    

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
        return {}, None

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
 
        # ExifTool devuelve una lista de diccionarios
        datos = json.loads(salida)
        print(datos)
        gps_info = datos[0]

        # Lógica para obtener las referencias.
        lat = gps_info.get('GPSLatitude')
        lon = gps_info.get('GPSLongitude')
        lat_ref = 'N' if float(lat) >= 0 else 'S'
        lon_ref = 'E' if float(lon) >=0 else 'W'

        fecha_str = gps_info.get('CreateDate')
        fecha = datetime.strptime(fecha_str, '%Y:%m:%d %H:%M:%S')

        gps_info = {
            'GPSLatitudeRef': lat_ref,
            'GPSLatitude': abs(float(lat)),
            'GPSLongitudeRef': lon_ref,
            'GPSLongitude': abs(float(lon)),
            'GPSDateStamp': fecha_str
        }        

        if any(v is None for v in gps_info.values()):
            gps_info = {}

        return gps_info, fecha

    except Exception as e:
        return {}, None


print(copia_binaria_fuerza("VID_20251024_205424.mp4", "C:\\FotosTemp"))

# Prueba con la ruta corregida
meta = {}
video_local = r"C:\FotosTemp\VID_20251024_205424.mp4"
meta, fecha = obtener_metadatos_reales(video_local)

print("*" * 30)
print(meta)
print(f'Fecha: {fecha}')
print("*" * 30)
