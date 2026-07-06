'''
Script en Python.
'''

from copia_clasificador_fotos import cargar_cache, guardar_cache

def cargar():
    return cargar_cache()

def guardar(cache):
    guardar_cache(cache)
