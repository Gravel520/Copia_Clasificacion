import subprocess # Ejecuta comandos externos como 'adb'.
import os # Gestiona rutas y archivos.
import shutil # Copia y elimina archivos.
import hashlib # Calcula hashes MD5 para detectar duplicados o eliminados.
import json # Carga y guarda datos en formato JSON.
from PyQt5.QtWidgets import QMessageBox
from PIL import Image # Abre imágenes y extrae metadatos EXIF.
from datetime import datetime # Maneja fechas.
from geopy.geocoders import Nominatim # Convierte coordenadas GPS en nombres de lugares.
from config_paths import ruta_adb, get_ruta_principal, get_ruta_temporal, ruta_movil, extensiones_validas
from pathlib import Path

# Inicializamos el servicio de Geolocalizador para convertir coordenadas
#   GPS en nombres de lugares.
geolocalizador = Nominatim(user_agent='copia_clasificador_fotos')

#===============================================================#
# UTILIDADES                                                    #
#===============================================================#

# Convierte coordenadas GPS en formato º, m y s, a grados decimales.
def convertir_a_grados(valor):
    d, m, s = valor
    return d + m / 60 + s / 3600

# Leemos el archivo JSON, si existe.
def cargar_json_unico(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Si no existe, lo creamos vacío
    data = {
        "clasificados": {"items": []},
        "pendientes": {"items": []},
        "eliminados": {"items": []},
        "stats": {
            "total_clasificados": 0,
            "total_pendientes": 0,
            "total_eliminados": 0
        }
    }
    guardar_json_unico(ruta, data)
    return data

# Guarda los datos en formato JSON.
def guardar_json_unico(ruta, data):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def comprobar_hash(hash_nuevo, lista_items):
    # Comprueba si un has ya existe en una lista.
    return not any(r["hash"] == hash_nuevo for r in lista_items)

# Comprobamos que un hash no esta en la lista de los archivos que
#   HEMOS ELIMINADO NOSOTROS.
def añadir_hash_eliminado(has_nuevo, lista_hashes):
    lista_hashes.append(has_nuevo)

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

                # Si todos los valores son None > no hay GPS real
                if all(v is None for v in gps_info.values()):
                    gps_info = {}

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
            ciudad = f'({partes[-4]})' # El nombre de la ciudad tendrá el será (ciudad)
            pais = f'({partes[-1]})' # El nombre del país será (pais)
            return f'{ciudad}{pais}', lat, lon
        
    except:
        pass

    return 'Sin_GPS'

# Usamos 'adb' para ejecutar 'stat' y obtener la fecha de creación del video.
def obtener_fecha_video(ruta_archivo):
    try:
        resultado = subprocess.run(
            [ruta_adb(), 'shell', f'stat -c %y "{ruta_archivo}"'],
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

# Ejecuta 'adb devices' y verifica si hay algún dispositivo conectado.
def hay_dispositivo_adb():
    dispositivos = subprocess.run([ruta_adb(), 'devices'], capture_output=True, text=True)
    lineas = dispositivos.stdout.strip().split('\n')
    # Ignora la cabecera y busca líneas con 'device' al final.
    dispositivos = [l for l in lineas[1:] if l.strip().endswith('device')]
    return len(dispositivos) > 0

def actualizar_stats(data):
    data["stats"]["total_clasificados"] = len(data["clasificados"]["items"])
    data["stats"]["total_pendientes"] = len(data["pendientes"]["items"])
    data["stats"]["total_eliminados"] = len(data["eliminados"]["items"])

def borrar_directorios_vacios():
    for subdir in Path(get_ruta_principal()).iterdir():
        if subdir.is_dir() and not any(subdir.iterdir()):
            subdir.rmdir()

#===============================================================#
# LISTAR ARCHIVOS                                               #
#===============================================================#

def obtener_archivos(ruta_pc=None):
    # Listar archivos desde el movil o pc.
    if ruta_pc:
        if os.path.exists(ruta_pc):
            return os.listdir(ruta_pc)
        return []

    if hay_dispositivo_adb():
        resultado = subprocess.run(
            [ruta_adb(), 'shell', f'ls {ruta_movil()}'],
            capture_output=True, text=True)
        return resultado.stdout.strip().split('\n')

    # No hay ningún movil conectado al ordenador.
    return []

#===============================================================#
# CLASIFICAR UN SOLO ARCHIVOS                                   #
#===============================================================#

def clasificar_archivo(archivo, ruta_archivos, data):
    mensaje = ""

    ruta_local = os.path.join(get_ruta_temporal(), archivo)
    ruta_origen = f'{ruta_archivos}/{archivo}'

    # Copiar o descargar
    if os.path.exists(ruta_origen):
        shutil.copy2(ruta_origen, ruta_local)
    else:
        return f"❌ No existe: {archivo}"

    # Obtención de los metadatos del gps y fecha.
    if archivo.lower().endswith(extensiones_validas("imagen")): # Archivos de imagen
        gps_info, fecha = obtener_datos_exif(ruta_local)
        ubicacion, lat, lon = obtener_ubicación(gps_info) if gps_info else ('(Sin_GPS)', 0, 0)

        # El string de la fecha será (año-mes)
        fecha_str = fecha.strftime('(%Y-%m)') if fecha else '(0000-00)'

    else: # Archivos de video
        try:
            fecha = obtener_fecha_video(ruta_origen)
            ubicacion, lat, lon = '(Sin_GPS)', 0, 0

            # El string de la fecha será (año-mes)
            fecha_str = fecha.strftime('(%Y-%m)') if fecha else '(0000-00)'
        except Exception as e:
            mensaje += f'💥 ({archivo}) No se puedo clasificar.\n'            

    # Crear carpeta destino.
    # Si NO hay ubicación, el nombre de la carpeta será, sólamente, '(Sin_GPS)'.
    if ubicacion == '(Sin_GPS)':
        nombre_carpeta = '(Sin_GPS)(Sin_GPS)(0000-00)'
    else:
        nombre_carpeta = f'{ubicacion}{fecha_str}'

    ruta_destino = os.path.join(get_ruta_principal(), nombre_carpeta)
    os.makedirs(ruta_destino, exist_ok=True)

    # Función obtener el hash del archivo.
    hash_archivo = calcular_hash_md5(ruta_local)

    # Creamos las listas separadas.
    clasificados = data["clasificados"]["items"]
    pendientes = data["pendientes"]["items"]
    eliminados = data["eliminados"]["items"]

    # Case 1 ➡ Sin GPS.
    if ubicacion == '(Sin_GPS)':

        # 1️⃣ Está en pendientes
        if not comprobar_hash(hash_archivo, pendientes):
            return f'❓ {archivo} - Pendiente de clasificar\n'

        # 2️⃣ Está en clasificados.
        if not comprobar_hash(hash_archivo, clasificados):
            return f'🔁 ({archivo}) Ya existe en clasificados\n'

        # 3️⃣ Está en eliminados
        if not comprobar_hash(hash_archivo, eliminados):
            return f'🟥 ({archivo}) Está eliminado\n'

        # 4️⃣ No está en ninguna lista ➡ añadir a pendientes
        shutil.copy2(ruta_local, ruta_destino)

        pendientes.append({
            'hash': hash_archivo,
            'ruta': os.path.join(ruta_destino, archivo),
            'ubicacion': '(Sin_GPS)',
            'fecha': fecha_str, # Grabamos la fecha para usarlo como ToolTip.
            'latitud': 0,
            'longitud': 0
        })

        return f'❓ {archivo} - Pendiente de clasificar\n'

    # Caso 2 ➡ Tiene ubicación.
    if comprobar_hash(hash_archivo, clasificados):
        # Comprobamos que el archivo NO este elimnado por nosotros.
        if comprobar_hash(hash_archivo, eliminados):

            # Comprobar que NO está en pendientes.
            if comprobar_hash(hash_archivo, pendientes):
                # Copiar archivo del directorio temporal al definitivo.
                shutil.copy2(ruta_local, ruta_destino)
                # Añadimos los datos al historial.
                clasificados.append({
                    'hash': hash_archivo,
                    'ruta': os.path.join(ruta_destino, archivo),
                    'ubicacion': ubicacion,
                    'fecha': fecha_str,
                    'latitud': float(lat),
                    'longitud': float(lon)
                })
                return f'🆗 {archivo} 🔜 {nombre_carpeta}\n'

            else:
                return f"🔁 ({archivo}) Estaba en pendientes\n"                        

        else:
            return f'🟥 ({archivo}) Archivo eliminado\n'

    return f'🔁 ({archivo}) Archivo duplicado\n'
