'''
Scrip en Python.

Recorremos la raís de backup y buscamos carpetas tipo
(ciudad)(pais)(fecha) sin archivos.
'''

import os

def check_directorios_vacios(raiz_backup):
    problemas = []

    for carpeta in os.listdir(raiz_backup):
        ruta_carpeta = os.path.join(raiz_backup, carpeta)
        if not os.path.isdir(ruta_carpeta):
            continue

        # Contar archivos dentro
        archivos = [
            f for f in os.listdir(ruta_carpeta)
            if os.path.isfile(os.path.join(ruta_carpeta, f))
        ]

        if len(archivos) == 0:
            problemas.append({
                "tipo": "directorio_vacio",
                "ruta": ruta_carpeta,
                "mensaje": "Carpeta sin archivos"
            })

    return {
        "nombre": "Directorios vacíos",
        "problemas": problemas
    }
