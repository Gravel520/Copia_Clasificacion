'''
Script en Python.
'''

import os
import shutil

from copia_clasificador_fotos import calcular_hash_md5

def borrar_archivo(ruta):
    if os.path.exists(ruta):
        os.remove(ruta)

def mover_archivo(origen, destino):
    shutil.move(origen, destino)

def calcular_hash(ruta):
    return calcular_hash_md5(ruta)
