'''
Script en Python
'''

from copia_clasificador_fotos import (
    cargar_json_unico, guardar_json_unico
)

def cargar_json(path):
    return cargar_json_unico(path)

def guardar_json(path, data):
    guardar_json_unico(path, data)
    