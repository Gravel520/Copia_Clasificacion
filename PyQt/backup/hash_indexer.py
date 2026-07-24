'''
Script en Python.
Este módulo se encarga de:
    · Recorrer una o varias rutas origen (PC, copia del móvil, etc).
    · Calcular el hash de cada archivo.
    · Guardar un índice: hash -> ruta.
    
'''

import os
import hashlib
from typing import Dict, List

def calcular_hash(ruta: str, bloque: int = 1024 * 1024) -> str:
    # Calcula el hash MD5 de un archivo.
    md5 = hashlib.md5()
    with open(ruta, "rb") as f:
        while True:
            data = f.read(bloque)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def crear_indice_hashes(rutas_origen: List[str]) -> Dict[str, List[str]]:
    '''
    Devuelve un índice:
    hash -> [rutas donde aparece ese archivo]
    '''
    indice: Dict[str, List[str]] = {}

    for raiz_origen in rutas_origen:
        for raiz, _, archivos in os.walk(raiz_origen):
            for nombre in archivos:
                ruta = os.path.join(raiz, nombre)

                try:
                    h = calcular_hash(ruta)
                except (OSError, PermissionError):
                    continue

                if h not in indice:
                    indice[h] = []

                indice[h].append(ruta)

    return indice

def buscar_por_hash(indice: Dict[str, List[str]], hash_objetivo: str) -> List[str]:
    return indice.get(hash_objetivo, [])

