'''
Script en Python.

'''

import subprocess
import os
import shutil
import hashlib
import json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from geopy.geocoders import Nominatim

ruta_movil = '/sdcard/DCIM/Camera'
ruta_pc = 'C:/Movil_Jesus_A33/Camera'
ruta_temporal = 'C:/FotosTemp'
ruta_final = 'C:/BackupFotos'
ruta_adb = 'C:\\adb\\platform-tools\\adb'
ruta_historial = './historial.json'
ruta_duplicados = './duplicados.json'
ruta_eliminados = './eliminados.json'

# Geolocalizador
geolocalizador = Nominatim(user_agent='clasificador_fotos')

def convertir_a_grados(valor):
    d, m, s = valor
    #return d[0]/d[1] + m[0]/d[1]/60 + s[0]/d[1]/360
    return d + m / 60 + s / 3600

def cargar_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r') as f:
            return json.load(f)
    return {}

def guardar_json(data, ruta):
    with open(ruta, 'w') as f:
        json.dump(data, f, indent=2)

'''
34853 - es el ID de GPSInfo
36867 - es el ID de DateTimeOriginal

Dentro de GPSInfo, los sub_IDs relevantes son:
1: 'GPSLatitudeRef' - Norte o Sur
2: 'GPSLatitude'
3: 'GPSLongitudeRef' - Este o West (Oeste)
4: 'GPSLongitude'
29: 'GPSDateStamp' (fecha sin hora)
'''
def obtener_datos_exif(imagen_path):
    try:
        imagen = Image.open(imagen_path)
        exif_data = imagen._getexif()
        gps_info = {}
        fecha = None
        
        if exif_data:
            # Obtener fecha original por ID 36867
            if 36867 in exif_data:
                fecha_str = exif_data[36867] # '2025:09:21 10:15:11'
                fecha = datetime.strptime(fecha_str, '%Y:%m:%d %H:%M:%S')
            
            # Obtener GPSInfo por ID 34853
            if 34853 in exif_data:
                gps_raw = exif_data[34853]
                gps_info = {
                    'GPSLatitudeRef': gps_raw.get(1),
                    'GPSLatitude': gps_raw.get(2),
                    'GPSLongitudeRef': gps_raw.get(3),
                    'GPSLongitude': gps_raw.get(4),
                    'GPSDateStamp': gps_raw.get(29)
                }

        return gps_info, fecha
    except Exception as e:
        print(f'Error al leer EXIF: {e}')
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
            ciudad = partes[-4]
            pais = partes[-1]
            return f'{ciudad}_{pais}'
    except:
        pass
    return 'Sin_GPS'

def obtener_fecha_video(ruta_archivo, nombre_archivo):
    try:
        resultado = subprocess.run(
            [ruta_adb, 'shell', f'stat -c &y {ruta_archivo}/{nombre_archivo}'],
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

def hay_dispositivo_adb():
    dispositivos = subprocess.run([ruta_adb, 'devices'], capture_output=True, text=True)
    lineas = dispositivos.stdout.strip().split('\n')
    # Ignora la cabecera y busca líneas con 'device' al final.
    dispositivos = [l for l in lineas[1:] if l.strip().endswith('device')]
    return len(dispositivos) > 0

def main():
    # Paso 1: Crear carpeta temporal
    os.makedirs(ruta_temporal, exist_ok=True)

    # Paso 2: Listar archivos en el movil o desde el pc.    
    if hay_dispositivo_adb():
        ruta_archivos = ruta_movil
        resultado = subprocess.run([ruta_adb, 'shell', f'ls {ruta_archivos}'],
                                capture_output=True,
                                text=True)
        archivos = resultado.stdout.strip().split('\n')
    else:    
        print('💻 No se puedo desde el movil, probar desde el PC...')
        ruta_archivos = ruta_pc
        archivos = os.listdir(ruta_archivos)

    # Paso 3: Descargar, comprobar duplicados y clasificar
    for archivo in archivos[:25]:
        if archivo.lower().endswith(('.jpg', '.jpeg', '.mp4')):
            ruta_origen = f'{ruta_archivos}/{archivo}'
            ruta_local = os.path.join(ruta_temporal, archivo)

            # Descargar archivo desde el movil o copiarlo desde el pc.
            if hay_dispositivo_adb():
                subprocess.run([ruta_adb, 'pull', ruta_origen, ruta_local])

            else:
                if os.path.exists(ruta_origen):
                    shutil.copy2(ruta_origen, ruta_local)

            # Clasificación
            if archivo.lower().endswith(('.jpg', '.jpeg')):
                gps_info, fecha = obtener_datos_exif(ruta_local)
                ubicacion = obtener_ubicación(gps_info) if gps_info else 'Sin_GPS'
                fecha_str = fecha.strftime('%Y-%m') if fecha else 'Sin_GPS'
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

if __name__ == '__main__':
    main()
