'''

'''

import win32com.client
import os
import time
import subprocess
import json
from datetime import datetime
from config_paths import (
    ruta_adb, ruta_movil, ruta_exiftools
)

def buscar_movil():
    shell = win32com.client.Dispatch("Shell.Application")
    este_equipo = shell.NameSpace(17)

    # 1. Buscar el móvil
    movil = next((i for i in este_equipo.Items() if "Galaxy A56 5G" in i.Name), None)
    return movil, shell

def listar_archivos_mtp():
    movil, shell = buscar_movil()

    if not movil:
        print("No se encontro ningún Movil.")
        return []
    
    try:
        # 2. Navegar hasta la carpeta Camera
        storage = movil.GetFolder.ParseName("Almacenamiento interno")
        if not storage: storage = movil.GetFolder.ParseName("Internal storage")

        dcim = storage.GetFolder.ParseName("DCIM")
        camera = dcim.GetFolder.ParseName("Camera")

        if not camera:
            return []
        
        # 3. Obtener todos los elementos y extraer sus nombre
        archivos = []
        for item in camera.GetFolder.Items():
            # Filtramos para no incluir subcarpetas, solo archivos
            if not item.IsFolder:
                archivos.append(item.Name)

        return archivos
    
    except Exception as e:
        print(f"Error al listar: {e}")
        return []

def copiar_archivo_mtp(nombre_archivo, carpeta_destino_pc):
    movil, shell = buscar_movil()

    if not movil:
        return "❌ No se encontró el Galaxy A56 5G en 'Este equipo'"

    try:
        # 2. IMPORTANTE: Usamos 'movil.GetFolder' (No dispositivo)
        storage = movil.GetFolder.ParseName("Almacenamiento interno")
        
        # Si tu Windows está en inglés, podría ser "Internal storage"
        if not storage:
            storage = movil.GetFolder.ParseName("Internal storage")
            
        if not storage:
            return "❌ No se pudo acceder al 'Almacenamiento interno'. ¿Está el móvil desbloqueado?"

        # 3. Navegamos por el resto de carpetas
        dcim = storage.GetFolder.ParseName("DCIM")
        camera = dcim.GetFolder.ParseName("Camera")
        
        if not camera:
            return "❌ No se encontró la carpeta DCIM/Camera"

        archivo_movil = camera.GetFolder.ParseName(nombre_archivo)
        
        if archivo_movil:
            # Aseguramos que la carpeta destino exista
            if not os.path.exists(carpeta_destino_pc):
                os.makedirs(carpeta_destino_pc)
                
            destino = shell.NameSpace(os.path.abspath(carpeta_destino_pc))
            
            # Copiamos (16 = Sobrescribir, 1024 = No mostrar errores de Windows)
            destino.CopyHere(archivo_movil, 16)
            
            # MTP es lento, damos un segundo para que Windows termine de soltar el archivo
            time.sleep(1) 
            
            return f"✅ Copiado con éxito (MTP + GPS): {nombre_archivo}"
        else:
            return f"❌ El archivo {nombre_archivo} no existe en la carpeta Camera"
            
    except Exception as e:
        return f"☠ Error navegando en MTP: {str(e)}"
    
def comprobar_movil_conectado():
    try:
        # Ejecutamos adb devices
        resultado = subprocess.run(
            [ruta_adb(), 'devices'],
            capture_output=True,
            text=True
        )
        lineas = resultado.stdout.strip().split('\n')

        # La primera línea es siempre "list of devices attached", la saltamos
        dispositivos = [linea for linea in lineas[1:] if 'device' in linea and 'offline' not in linea]

        if dispositivos:
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def copia_binaria_fuerza(archivo, carpeta_destino_pc):
    ruta_origen = f"{ruta_movil()}/{archivo}"

    if not os.path.exists(carpeta_destino_pc):
        os.makedirs(carpeta_destino_pc)

    comando = f'{ruta_adb()} pull -a "{ruta_origen}" "{carpeta_destino_pc}"'

    try:
        subprocess.run(comando, shell=True)
        return True
    except:
        return False

def obtener_metadatos_reales(ruta_archivo):
    # Verificamos si el archivo de video existe antes de llamar a exiftool
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo no existe en {ruta_archivo}")
        return {}, None

    comando = [
        ruta_exiftools(), 
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
        gps_info = datos[0]

        #fecha_str = gps_info['CreateDate']
        #fecha = datetime.strptime(fecha_str, '%Y:%m:%d %H:%M:%S')
        fecha_str = gps_info.get('CreateDate')
        fecha = None
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y:%m:%d %H:%M:%S')
            except:
                fecha = None

        # Lógica para obtener las referencias.
        lat = gps_info.get('GPSLatitude')
        lon = gps_info.get('GPSLongitude')

        # Si falta cualquiera -> devolver vacío
        if lat is None or lon is None:
            return {}, fecha
        
        # Convertir con seguridad
        try:
            lat = float(lat)
            lon = float(lon)
        except:
            return {}, fecha
        
        gps_info = {
            'GPSLatitudeRef': 'N' if lat >= 0 else 'S',
            'GPSLatitude': abs(float(lat)),
            'GPSLongitudeRef': 'E' if lon >= 0 else 'W',
            'GPSLongitude': abs(float(lon)),
            'GPSDateStamp': fecha_str
        }

        return gps_info, fecha

    except Exception as e:
        print(f"Error al ejecutar ExifTool: {e}")
        return {}, None

# Función para obtener una lista con los nombres de los archivos.
def obtener_archivos_movil():
    resultado = subprocess.run([ruta_adb(), 'shell', f'ls {ruta_movil()}'], 
                               capture_output=True,
                               text=True)
    return resultado.stdout.strip().split('\n')
