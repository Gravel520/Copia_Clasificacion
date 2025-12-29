'''
Script en Python. Este programa en Python automatiza la descarga, clasificación
y respaldo de fotos y videos desde un móvil Android conectado por USB o 
desde una carpeta local en el PC. También detecta duplicados  o eliminados por
nosotros usando hashes, y organiza los archivos por ubicación GPS y fecha.

En la función principal 'main', tenemos el siguiente bloque de código
que empieza con un bucle for, y es el encargado de gestionar todos los
archivos seleccionados, ya sea desde el movil o del Pc.
1º Comprobamos que el archivo sea una imagen o un video.
2º Creamos las rutas de origen del archivo (movil o pc), y la ruta 
    temporal (pc).
3º Descargamos el archivo desde el movil o lo copiamos desde el pc a
    la ruta temporal.
4º Si el archivo es una imagen:
    - Obtenemos los datos del gps y la fecha a través de los metadatos.
    - Obtenemos la ubicación 'ciudad_pais' de los datos gps.
    - Convertimos la fecha en un string con el formato 'año_mes'
    Si el archivo es un video:
    - Sólamente se puede extraer la fecha del video, pero además si es
        desde el movil, si la obtendremos verdadera, pero desde el pc puede
        ser la fecha al haberlo copiado o movido, así que es mejor no
        obtenerla si es un archivo desde el pc.
5º Creamos la carpeta de destino a través de las variables de ubicación
    '(ciudad)(pais)' y de la fecha '(año_mes)'.
6º Comprobamos que el archivo que se encuentra en la carpeta temporal y 
    que estamos gestionando, no tiene su hash-mh5, ni en el historial
    de existentes, con lo cual estaríamos duplicándolo, ni en el eliminados,
    que serán los que hallamos borrado nosotros porque no nos interesa.
    - Si no esta ni duplicado y eliminado, se copia.

Una vez finalizado el bucle, se actualiza los archivos .json de duplicados
y eliminados, es decir, se actualizan las listas.
Por último se borra el directorio temporal con todos sus archivos.
'''

import subprocess # Ejecuta comandos externos como 'adb'.
import os # Gestiona rutas y archivos.
import shutil # Copia y elimina archivos.
import hashlib # Calcula hashes MD5 para detectar duplicados o eliminados.
import json # Carga y guarda datos en formato JSON.
from PyQt5.QtWidgets import QMessageBox
from PIL import Image # Abre imágenes y extrae metadatos EXIF.
from datetime import datetime # Maneja fechas.
from geopy.geocoders import Nominatim # Convierte coordenadas GPS en nombres de lugares.
from config import *
from pathlib import Path

ruta_movil = RUTA_MOVIL
#ruta_pc = RUTA_PC
ruta_temporal = RUTA_TEMPORAL
ruta_final = RUTA_PRINCIPAL
ruta_adb = RUTA_ADB
#ruta_historial = RUTA_HISTORIAL
ruta_duplicados = HISTORIAL
ruta_eliminados = RUTA_ELIMINADOS
ruta_pendientes = PENDIENTES


# Inicializamos el servicio de Geolocalizador para convertir coordenadas
#   GPS en nombres de lugares.
geolocalizador = Nominatim(user_agent='copia_clasificador_fotos')

# Convierte coordenadas GPS en formato º, m y s, a grados decimales.
def convertir_a_grados(valor):
    d, m, s = valor
    return d + m / 60 + s / 3600

# Leemos el archivo JSON, si existe.
def cargar_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def comprobar_hash(hash_nuevo, lista_hashes):
    '''
    Comprobamos si un hash esta en la lista de duplicados o eliminados.
    Dependiendo del valor del parámetro 'lista_hashes', que sea
        duplicados o eliminados.
    '''
    if any(r['hash'] == hash_nuevo for r in lista_hashes):
        return False
    
    else:
        return True

# Comprobamos que un hash no esta en la lista de los archivos que
#   HEMOS ELIMINADO NOSOTROS.
def añadir_hash_eliminado(has_nuevo, lista_hashes):
    lista_hashes.append(has_nuevo)

# Guarda los datos en formato JSON.
def guardar_json(data, ruta):
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

'''
Extraemos los metadatos EXIF de la fecha original y de las coordenadas
GPS, y devolvemos ambos datos.
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
    
'''
Conversión de coordenadas a ubicación.
1º Convertimos latitud y longitud a grados decimales.
2º Ajustamos el signo según el hemisferio.
3º Usamos 'geopy' para obtener ciudad y país.
4º Devolvemos una cadena como 'Madrid_España'.
'''
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

# Ejecuta 'adb devices' y verifica si hay algún dispositivo conectado.
def hay_dispositivo_adb():
    dispositivos = subprocess.run([ruta_adb, 'devices'], capture_output=True, text=True)
    lineas = dispositivos.stdout.strip().split('\n')
    # Ignora la cabecera y busca líneas con 'device' al final.
    dispositivos = [l for l in lineas[1:] if l.strip().endswith('device')]
    return len(dispositivos) > 0

def borrar_directorios_vacios():
    '''
    Con esta función comprobamos que no se han creado directorios vacíos
    al momento de copiar y clasificar, ya que primero se crea el directorio
    y luego se comprueba si ese archivo está duplicado, eliminado o no
    se puede clasificar. Así que el directorio persiste.
    '''
    for subdir in Path(RUTA_PRINCIPAL).iterdir():
        if subdir.is_dir():
            if not any(subdir.iterdir()):
                subdir.rmdir()
                
# Función principal.
def main(ruta_pc=None):
    # Definimos la variable del mensaje que vamos a retornar,
    #   y el número de archivos copiados.
    mensaje = ''
    num_copiados = 0

    # Crear carpeta temporal.
    os.makedirs(ruta_temporal, exist_ok=True)

    # Cargamos el historial de duplicados y eliminados.
    duplicados = cargar_json(ruta_duplicados)
    eliminados = cargar_json(ruta_eliminados)
    pendientes = cargar_json(ruta_pendientes)

    # Listar archivos desde el movil o pc.
    if ruta_pc:
        ruta_archivos = ruta_pc
        if os.path.exists(ruta_archivos):
            archivos = os.listdir(ruta_archivos)
        else:
            return f"La ruta {ruta_archivos} no existen en el PC.", 0
    else:
        if hay_dispositivo_adb():
            ruta_archivos = ruta_movil
            resultado = subprocess.run([ruta_adb, 'shell', f'ls {ruta_archivos}'],
                                    capture_output=True,
                                    text=True)
            archivos = resultado.stdout.strip().split('\n')
        else:
            # No hay ningún movil conectado al ordenador.
            return "No hay ningún móvil conectado al ordenador.", 0

    # Descargar, comprobar duplicados y clasificar.
    for archivo in archivos[:30]:
        if archivo.lower().endswith(('.jpg', '.jpeg', '.mp4')):
            ruta_origen = f'{ruta_archivos}/{archivo}'
            ruta_local = os.path.join(ruta_temporal, archivo)

            # Descargar archivo desde el movil o copiarlo desde el pc al directorio temporal.
            if ruta_pc:
                if os.path.exists(ruta_origen):
                    shutil.copy2(ruta_origen, ruta_local)
                else:
                    return "La ruta seleccionada en el PC no existe.", 0
            else:
                if hay_dispositivo_adb():
                    subprocess.run([ruta_adb, 'pull', ruta_origen, ruta_local])
                else:
                    return "No se encontró ninguna fuente válida para copiar.", 0               

            # Obtención de los metadatos del gps y fecha.
            if archivo.lower().endswith(('.jpg', '.jpeg')):
                gps_info, fecha = obtener_datos_exif(ruta_local)
                if gps_info:
                    ubicacion, lat, lon = obtener_ubicación(gps_info)
                else:
                    ubicacion, lat, lon = '(Sin_GPS)', 0, 0
                # El string de la fecha será (año-mes)
                fecha_str = fecha.strftime('(%Y-%m)') if fecha else '(Sin_Fecha)'

            else: # .mp4                
                try:
                    fecha = obtener_fecha_video(ruta_local)
                    ubicacion, lat, lon = '(Sin_GPS)', 0, 0

                    # El string de la fecha será (año-mes)
                    fecha_str = fecha.strftime('(%Y-%m)') if fecha else '(Sin_Fecha)'
                except Exception as e:
                    mensaje += f'💥 ({archivo}) No se puedo clasificar.\n'
                    continue

            # Crear carpeta destino.
            # Si NO hay ubicación, el nombre de la carpeta será, sólamente, '(Sin_GPS)'.
            if ubicacion == '(Sin_GPS)':
                nombre_carpeta = '(Sin_GPS)(Sin_GPS)(0000-00)'
            else:
                nombre_carpeta = f'{ubicacion}{fecha_str}'
            ruta_destino = os.path.join(ruta_final, nombre_carpeta)
            os.makedirs(ruta_destino, exist_ok=True)

            # Función obtener el hash del archivo.
            hash_archivo = calcular_hash_md5(ruta_local)

            # Comprobamos si el archivo tienen ubicación, para grabarlo en 
            #   'pendientes'.
            if ubicacion == '(Sin_GPS)':
                if comprobar_hash(hash_archivo, pendientes):
                    shutil.copy2(ruta_local, ruta_destino)
                    pendientes.append({
                        'hash': hash_archivo,
                        'ruta': os.path.join(ruta_destino, archivo),
                        'ubicacion': '(Sin_GPS)',
                        'fecha': '(0000-00)',
                        'latitud': 0,
                        'longitud': 0
                    })
                    mensaje += f'❓ {archivo} - Pendiente de clasificar\n'

            else:
                if comprobar_hash(hash_archivo, duplicados):
                    # Comprobamos que el archivo NO este elimnado por nosotros.

                    # CÓDIGO PARA COMPROBAR SI ESTA EN EL JSON DE PENDIENTES.

                    if comprobar_hash(hash_archivo, eliminados):
                        # Copiar archivo del directorio temporal al definitivo.
                        shutil.copy2(ruta_local, ruta_destino)
                        # Añadimos los datos al historial.
                        duplicados.append({
                            'hash': hash_archivo,
                            'ruta': os.path.join(ruta_destino, archivo),
                            'ubicacion': ubicacion,
                            'fecha': fecha_str,
                            'latitud': float(lat),
                            'longitud': float(lon)
                        })
                        mensaje += f'🆗 {archivo} 🔜 {nombre_carpeta}\n'
                        num_copiados += 1

                    else:
                        mensaje += f'🟥 ({archivo}) Archivo eliminado\n'

                else:
                    mensaje += f'🔁 ({archivo}) Archivo duplicado o eliminado\n'

    # Guardamos la lista de duplicados y eliminados.
    guardar_json(duplicados, ruta_duplicados)
    guardar_json(eliminados, ruta_eliminados)
    guardar_json(pendientes, ruta_pendientes)

    # Limpiar carpeta temporal
    shutil.rmtree(ruta_temporal)

    # Limpiar carpetas vacías.
    borrar_directorios_vacios()

    # Devolvemos el mensaje con la acción realizada,
    #   copiado o no copiado.
    return mensaje, num_copiados

# Ejecutamos el script.
if __name__ == '__main__':
    main()
