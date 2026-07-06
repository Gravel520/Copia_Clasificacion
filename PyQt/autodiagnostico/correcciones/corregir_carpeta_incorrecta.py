'''
Script en Python.
'''

import os
import shutil

from autodiagnostico.chequeos.json_vs_carpetas import construir_nombre_carpeta

def corregir_carpeta_incorrecta(lista_problemas, data, raiz_backup):
    for p in lista_problemas:
        ruta = p.get("ruta")
        carpeta_esperada = p.get("carpeta_esperada")

        carpeta_correcta = os.path.join(raiz_backup, carpeta_esperada)
        os.makedirs(carpeta_correcta, exist_ok=True)

        destino = os.path.join(carpeta_correcta, os.path.basename(ruta))
        shutil.move(ruta, destino)

    return data
