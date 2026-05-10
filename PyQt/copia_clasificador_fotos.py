import subprocess # Ejecuta comandos externos como 'adb'.
import os # Gestiona rutas y archivos.
import shutil # Copia y elimina archivos.
import hashlib # Calcula hashes MD5 para detectar duplicados o eliminados.
import json # Carga y guarda datos en formato JSON.
import unicodedata
from PIL import Image # Abre imágenes y extrae metadatos EXIF.
from datetime import datetime # Maneja fechas.
from geopy.distance import geodesic # Calcula la distancia.
from config_paths import (ruta_adb, get_ruta_principal, get_ruta_temporal, 
                          ruta_movil, extensiones_validas, ruta_json_miniaturas,
                          get_ruta_miniaturas, geocodificador)
from pathlib import Path
from utils.utils_cache import (
    cargar_cache, guardar_cache, normalizar_texto
)
from utils.utils_exif import (
    buscar_movil, listar_archivos_mtp, copiar_archivo_mtp,
    obtener_metadatos_reales, copia_binaria_fuerza,
    obtener_archivos_movil, comprobar_movil_conectado
)

# Inicializamos el servicio de Geolocalizador para convertir coordenadas
#   GPS en nombres de lugares.
geolocalizador, reverse = geocodificador()

#===============================================================#
# UTILIDADES                                                    #
#===============================================================#

# Convierte coordenadas GPS en formato º, m y s, a grados decimales.
def convertir_a_grados(valor):
    # Si el valor ya es un número (int o float), son grados decimales
    if isinstance(valor, (int, float)):
        return valor
    
    # Si es una secuencia (tupla o lista), asume formato (d, m, s)
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

def cargar_json_miniaturas(ruta: Path):
    if ruta.exists():
        return json.loads(ruta.read_text())
    return {"miniaturas": []}

def guardar_json_miniaturas(ruta: Path, data):
    ruta.write_text(json.dumps(data, indent=4))

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
                if any(v is None for v in gps_info.values()):
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

        # Reverse geocoding
        ubicacion = reverse((lat, lon), language='es', exactly_one=True)
        if not ubicacion:
            return "Sin_GPS"

        datos = ubicacion.raw.get("address", {})
        ciudad = datos.get("city") or datos.get("town") or datos.get("village")
        pais = datos.get("country_code", "").upper()

        # Validación: si el pais no es ES, FR o PT > comprobar
        paises_validos = ["ES", "FR", "PT"]

        if pais not in paises_validos:
            # Intentamos encontrar la ciudad en los países válidos
            for p in paises_validos:
                consulta = f"{ciudad}, {p}"
                posible = geolocalizador.geocode(consulta, language="es")

                if posible:
                    dist = geodesic((lat, lon), (posible.latitude, posible.longitude)).km
                    if dist < 100: # Distancia razonable
                        return f'({ciudad}({p}))', lat, lon
            # Si ninguna coincide > GPS incorrecto
            return "Sin_GPS"
        
        # Si el país es válido, devolvemos directamente
        return f'({normalizar_texto(ciudad)})({normalizar_texto(datos.get("country"))})', lat, lon
        
    except Exception as e:
        print("Error GPS: ", e)

    return 'Sin_GPS'

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
    else:
        return obtener_archivos_movil()

#===============================================================#
# CLASIFICAR UN SOLO ARCHIVOS                                   #
#===============================================================#

def clasificar_archivo(archivo, ruta_archivos, data):
    ruta_local = os.path.join(get_ruta_temporal(), archivo)
    ruta_origen = f'{ruta_archivos}/{archivo}'

    try:
        # Copiar desde movil
        if comprobar_movil_conectado():
            copia_binaria_fuerza(archivo, get_ruta_temporal())

        else:
            # Copiar desde pc.
            if os.path.exists(ruta_origen):
                shutil.copy2(ruta_origen, ruta_local)
            else:
                return f"❌ Error al copiar desde PC: {archivo}\n"
            
    except Exception as e:
        return f"☠ Error inesperado al copiar archivo: {str(e)}"

    # Función obtener el hash del archivo.
    hash_archivo = calcular_hash_md5(ruta_local)    

    # Obtención de los metadatos del gps y fecha.
    if archivo.lower().endswith(extensiones_validas("imagen")): # Archivos de imagen
        gps_info, fecha = obtener_datos_exif(ruta_local)
        ubicacion, lat, lon = obtener_ubicación(gps_info) if gps_info else ('(Sin_GPS)', 0, 0)

        # Actualizar cache geocoding.
        actualizar_cache_geocoding(ubicacion, lat, lon)

        # El string de la fecha será (año-mes)
        fecha_str = fecha.strftime('(%Y-%m)') if fecha else '(0000-00)'

        # Para agrupar por fecha del archivo
        fecha_completa, timestamp, hora = agrupar_fecha_archivo(ruta_origen, fecha)

    else: # Archivos de video
        try:
            gps_info, fecha = obtener_metadatos_reales(ruta_local)
            ubicacion, lat, lon = obtener_ubicación(gps_info) if gps_info else ('(Sin_GPS)', 0, 0)

            # Actualizar cache geocoding.
            actualizar_cache_geocoding(ubicacion, lat, lon)
            
            # El string de la fecha será (año-mes)
            fecha_str = fecha.strftime('(%Y-%m)') if fecha else '(0000-00)'

            # Para agrupar por fecha del archivo
            fecha_completa, timestamp, hora = agrupar_fecha_archivo(ruta_local, fecha)

        except Exception as e:
            return f'💥 ({archivo}) No se puedo clasificar.\n'            

    # Crear carpeta destino.
    # Si NO hay ubicación, el nombre de la carpeta será, sólamente, '(Sin_GPS)'.
    if ubicacion == '(Sin_GPS)':
        nombre_carpeta = '(Sin_GPS)(Sin_GPS)(0000-00)'
    else:
        nombre_carpeta = f'{ubicacion}{fecha_str}'

    ruta_destino = os.path.join(get_ruta_principal(), nombre_carpeta)
    os.makedirs(ruta_destino, exist_ok=True)

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

        if archivo.lower().endswith(extensiones_validas("video")): # Archivos de video
            # Obtenemos o creamos la miniatura del video.
            obtener_miniaturas(ruta_local, hash_archivo)

        # 4️⃣ No está en ninguna lista ➡ añadir a pendientes
        shutil.copy2(ruta_local, ruta_destino)

        pendientes.append({
            'hash': hash_archivo,
            'ruta': os.path.join(ruta_destino, archivo),
            'ubicacion': '(Sin_GPS)',
            'fecha': fecha_str, # Grabamos la fecha para usarlo como ToolTip.
            'fecha_completa': fecha_completa, # YYYY-MM-DD
            'hora': hora, # HH:MM:SS
            'timestamp': timestamp,
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
                if archivo.lower().endswith(extensiones_validas("video")): # Archivos de video
                    # Obtenemos o creamos la miniatura del video.
                    obtener_miniaturas(ruta_local, hash_archivo)

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

def agrupar_fecha_archivo(ruta_origen, fecha):    
    if not fecha: # Para agrupar por fecha del archivo
        timestamp = os.path.getmtime(ruta_origen)
        fecha_completa = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        hora = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
    else:
        # String de la fecha, hora y timestamp para clasificación por lotes
        fecha_completa = fecha.strftime('%Y-%m-%d') if fecha else '0000-00-00'
        hora = fecha.strftime('%H:%M:%S') if fecha else '00:00:00'
        timestamp = int(fecha.timestamp()) if fecha else 0

    return fecha_completa, timestamp, hora

'''
Para extraer las miniaturas de los archivos de video, se utiliza una
aplicación externa que hay que colocar en el ordenador. ffmpeg, se 
descarga desde esta página "https://www.gyan.dev/ffmpeg/builds/".
Hay que seleccionar la descarga "ffmpeg-xxxx-full_build/", extraerlo 
en c:\ffmpeg\ y colocarlo en el PATH del ordenador.
'''
def obtener_miniaturas(ruta_origen, hash):
    FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe" # Extraer fotograma
    FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe" # Obtener duración del video

    try:
        # Crear carpeta miniaturas si no existe
        ruta_miniaturas = get_ruta_miniaturas()
        ruta_miniaturas.mkdir(parents=True, exist_ok=True)

        # Rutas de salida
        ruta_salida = ruta_miniaturas / f"{hash}.jpg"
        ruta_temp = ruta_miniaturas / f"{hash}_temp.jpg"

        # Obtener duración del video con ffprobe
        resultado = subprocess.run([
            FFPROBE, "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(ruta_origen)
        ], capture_output=True, text=True, check=True)

        duracion = float(resultado.stdout.strip())

        # Decidir el segundo
        tiempo_miniatura = "00:00:05" if duracion >= 5 else "00:00:01"

        # Extraer fotograma
        subprocess.run([
            FFMPEG, "-y",
            "-ss", tiempo_miniatura,
            "-i", str(ruta_origen),
            "-vframes", "1",
            "-vf", "format=yuv420p",
            str(ruta_temp)
        ], check=True)

        marca = Path(__file__).parent / "assets" / "marca_video.png"

        # Añadir marca de agua con imagen PNG
        subprocess.run([
            FFMPEG, "-y",
            "-i", str(ruta_temp),
            "-i", str(marca),
            "-filter_complex",
            # Escalar marca al 40% del ancho de la imagen
            "[1:v]scale=iw*0.4:-1[wm];"
            # Colocar marca en el centro
            "[0:v][wm]overlay=(W-w)/2:(H-h)/2",
            str(ruta_salida)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Borrar temporal
        ruta_temp.unlink(missing_ok=True)

        # Registrar en JSON
        data = cargar_json_miniaturas(ruta_json_miniaturas())
        if hash not in data["miniaturas"]:
            data["miniaturas"].append(hash)
            guardar_json_miniaturas(ruta_json_miniaturas(), data)

        return True

    except Exception as e:
        print(f"Error generando miniatura: {e}")
        return False
    
def normalizar_texto(t):
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))

def actualizar_cache_geocoding(ubicacion, lat, lon):
    if ubicacion != '(Sin_GPS)':
        clave_norm = normalizar_texto(ubicacion)
        cache_geocoding = cargar_cache()

        # Solo guardar si no existe
        if clave_norm not in cache_geocoding:
            cache_geocoding[clave_norm] = [float(lat), float(lon)]
            guardar_cache(cache_geocoding)
