'''
Script en Python.
Aquí vamos a obtener los datos 'exif' de una imagen, concretamente la
latitud y la longitud, para después poder convertirlo en coordenada
válidas para poder utilizarlo con el módulo 'folium'.
El id de los datos exif correspondiente a las coordenadas es el número
34853, en sus órdenes del 1 al 4, y no la leyenda 'GPSInfo'. Tampoco los
órdenes son 'GPSLatitude', etc...
'''

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fractions import Fraction

def convertir_a_decimal(dms, ref):
    grados, minutos, segundos = dms
    decimal = grados + minutos / 60 + segundos / 3600
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def validar_coordenadas(valor):
    if isinstance(valor, Fraction):
        return float(valor)
    elif isinstance(valor, tuple):
        return float(Fraction(valor[0], valor[1]))
    elif isinstance(valor, str) and '/' in valor:
        return float(Fraction(valor))
    else:
        raise TypeError(f"Formato de coordenada no reconocido: {valor}")
    
def extraer_gps(exif_data):
    if not exif_data:
        print('No hay metadatos EXIF.')
        return None
    
    gps_info = exif_data.get(34853)
    if not gps_info:
        print('No hay datos GPS.')
        return None
    
    try:
        lat_ref = gps_info[1] # Latitud 'N' o 'S'
        lat_dms = gps_info[2] # Coordenada de latitud
        lon_ref = gps_info[3] # Longitud 'E' o 'W'
        lon_dms = gps_info[4] # Coordenada de longitud

        latitud = convertir_a_decimal(lat_dms, lat_ref)
        longitud = convertir_a_decimal(lon_dms, lon_ref)

        return latitud, longitud
    
    except KeyError as e:
        print(f'Falta una clave GPS: {e}')
        return None
    
# Ruta de la imagen
imagen_path = 'C:/BackupFotos/Sin_GPS_&Y-05/IMG_20250506_102006.jpg'

# Abrir imagen y extraer EXIF
imagen = Image.open(imagen_path)
exif_data = imagen._getexif()

# Extraer coordenadas GPS
coordenadas = extraer_gps(exif_data)

if coordenadas:
    latitud = validar_coordenadas(coordenadas[0])
    longitud = validar_coordenadas(coordenadas[1])
    print(f'📍 Coordenadas GPS:\nLatitud: {latitud}\nLongitud: {longitud}')
else:
    print('No se pudieron extraer coordenadas GPS.')
