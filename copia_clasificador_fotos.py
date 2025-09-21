'''
Script en Python.

'''

import subprocess
import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from geopy.geocoders import Nominatim
import shutil
import hashlib

ruta_movil = '/sdcard/DCIM/Camera'
ruta_temporal = 'C:/FotosTemp'
ruta_final = 'C:/BackupFotos'
ruta_adb = 'C:\\adb\\platform-tools\\adb'

# Geolocalizador
geolocalizador = Nominatim(user_agent='clasificador_fotos')

# Paso 1: Crear carpeta temporal
os.makedirs(ruta_temporal, exist_ok=True)

# Paso 2: Listar archivos en el movil
resultado = subprocess.run([ruta_adb, 'shell', f'ls {ruta_movil}'],
                           capture_output=True,
                           text=True)
archivos = resultado.stdout.strip().split('\n')

def convertir_a_grados(valor):
    d, m, s = valor
    return d[0]/d[1] + m[0]/d[1]/60 + s[0]/d[1]/360

def obtener_datos_exif(imagen_path):
    try:
        imagen = Image.open(imagen_path)
        exif_data = imagen._getexif()
        gps_info = {}
        fecha = None
        if exif_data:
            for tag_id, valor in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    fecha = datetime.strptime(valor, '%Y:%m:%d %H:%M:%S')
                elif tag == 'GPSInfo':
                    for key in valor:
                        sub_tag = GPSTAGS.get(key, key)
                        gps_info[sub_tag] = valor[key]
        return gps_info, fecha
    except:
        return {}, None
    
def obtener_ubicación(gps_info):
    try:
        lat = convertir_a_grados(gps_info['GPSLatitude'])
        lon = convertir_a_grados(gps_info['GPSLongitude'])
        if gps_info['GPSLatitudeRef'] != 'N':
            lat = -lat
        if gps_info['GPSLongitudeRef'] != 'E':
            lon = -lon
        ubicacion = geolocalizador.reverse((lat, lon), language='es')
        if ubicacion:
            partes = ubicacion.address.split(', ')
            ciudad = partes[0]
            pais = partes[-1]
            return f'{ciudad}_{pais}'
    except:
        pass
    return 'Sin_GPS'

def obtener_fecha_video(nombre_archivo):
    try:
        resultado = subprocess.run(
            [ruta_adb, 'shell', f'stat -c &y {ruta_movil}/{nombre_archivo}'],
            capture_output=True, text=True
        )
        fecha_raw = resultado.stdout.strip()
        fecha_obj = datetime.strptime(fecha_raw[:10], '%Y-%m-%d')
        return fecha_obj
    except:
        return None
    
# Comprobar archivos duplicados a través de su hash.
def calcular_hash_md5(ruta_archivo):
    try:
        hash_md5 = hashlib.md5()
        with open(ruta_archivo, 'rb') as f:
            for bloque in iter(lambda: f.read(4096), b''):
                hash_md5.update(bloque)
        return hash_md5.hexdigest()
    except:
        return None
    
def existe_duplicado(ruta_destino, hash_nuevo):
    for archivo in os.listdir(ruta_destino):
        ruta_existente = os.path.join(ruta_destino, archivo)
        if os.path.isfile(ruta_existente):
            hash_existente = calcular_hash_md5(ruta_existente)
            if hash_existente == hash_nuevo:
                return True
    return False

# Paso 3: Descargar, comprobar duplicados y clasificar
for archivo in archivos:
    if archivo.lower().endswith(('.jpg', '.jpeg', '.mp4')):
        ruta_origen = f'{ruta_movil}/{archivo}'
        ruta_local = os.path.join(ruta_temporal, archivo)

        # Descargar archivo
        subprocess.run([ruta_adb, 'pull', ruta_origen, ruta_local])

        # Clasificación
        if archivo.lower().endswith(('.jpg', '.jpeg')):
            gps_info, fecha = obtener_datos_exif(ruta_local)
            ubicacion = obtener_ubicación(gps_info) if gps_info else 'Sin_GPS'
            fecha_str = fecha.strftime('&Y-%m') if fecha else 'Sin_GPS'
        else: # .mp4
            fecha = obtener_fecha_video(archivo)
            ubicacion = 'Sin_GPS'
            fecha_str = fecha.strftime('%Y-%m') if fecha else 'Sin_GPS'

        # Crear carpeta destino
        nombre_carpeta = f'{ubicacion}_{fecha_str}'.replace(' ', '_').replace(",", "")
        ruta_destino = os.path.join(ruta_final, nombre_carpeta)
        os.makedirs(ruta_destino, exist_ok=True)

        # Función archivo duplicado.
        hash_archivo = calcular_hash_md5(ruta_local)
        if existe_duplicado(ruta_destino, hash_archivo):
            print(f'🔁 Duplicado detectado: {archivo} - no se copia...')
            continue

        # Copiar archivo
        shutil.copy2(ruta_local, ruta_destino)
        print(f'{archivo} ➡ {nombre_carpeta}')

# Limpiar carpeta temporal
shutil.rmtree(ruta_temporal)

