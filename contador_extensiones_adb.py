'''
Script en Python. Este script lo usamos como prueba para comprobar
la conectividad entre el Pc y el movil a través del puerto USB.
Su función es entrar en un directorio en concreto y contar las
extensiones de tipo gráfico que hay (jpg, jpeg y mp4).

El módulo 'subprocess', nos permite ejecutar comandos externos, como
    'adb', desde Python.

Función (obtener_archivos):
El comando que ejecutamos mediante el módulo anterior 'adb shell ls /sdcard/DCIM/Camera',
    lista los archivos en esa carpeta, guarda la salida del comando y
    convierte la salida en texto legible, en lugar de bytes.
Lo que retornamos es lo siguiente:
    resultado.stdout - contiene la lista de archivos como una cadena.
    strip() - elimina espacios o saltos de línea al principio y al final.
    split('\n') - convierte la cadena en una lista de nombres de archivo.

Función (contar_extensiones):
'Counter', simplifica el conteo.
Se usa 'os.path.splitext()' para extraer la extensión del archivo, que se
    convierte en minúsculas para evitar errores por mayúsculas.
    Usamos 'Counter[ext]' para contar cuántos archivos hay de cada tipo.
    Si la extensión no es la definida, lo califica como 'otro' y lo añade
    a una lista para, posteriormente, listarlo y analizarlo.
'''

# Importar las extensiones
import os
import subprocess
from subprocess import SubprocessError
from collections import Counter

ruta_movil = '/sdcard/DCIM/Camera'

# Función para obtener una lista con los nombres de los archivos.
def obtener_archivos(ruta_adb, ruta_movil):
    resultado = subprocess.run([ruta_adb, 'shell', f'ls {ruta_movil}'], 
                               capture_output=True,
                               text=True)
    return resultado.stdout.strip().split('\n')

# Función para contar las extensiones que definamos
def contar_extensiones(archivos):
    contador = Counter()
    otros = []

    for archivo in archivos:
        ext = os.path.splitext(archivo.lower())[1]
        if ext in ['.jpg', '.jpeg', '.mp4']:
            contador[ext] += 1
        else:
            otros.append(archivo)
            contador['otro'] += 1

    return contador, otros

# Llamamos a la función que ejecuta el subproceso para obtener los archivos
#   de la ubicación definida del movil.
try:
    archivos = obtener_archivos('C:\\adb\\platform-tools\\adb', ruta_movil)
except SubprocessError as e:
    print(f'Error al ejecutar ADB: {e}')
    archivos = []

# Llamamos a la función para contar las extensiones, e imprimos los resultados.
contador, otros = contar_extensiones(archivos)

print(f'Total archivos: {len(archivos)}')
for ext in ['.jpg', '.jpeg', '.mp4', 'otro']:
    print(f'{ext}: {contador.get(ext, 0)}')

if otros:
    print('\nArchivos con extensiones no reconocidas:')
    for archivo in otros:
        print(f' - {archivo}')
