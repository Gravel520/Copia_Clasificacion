'''
Script en Python.
'''

import os

def carpeta_de_ruta(ruta):
    return os.path.basename(os.path.dirname(ruta))
