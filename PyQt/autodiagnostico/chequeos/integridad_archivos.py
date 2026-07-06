'''
Script en Python.

Aquí comprobamos:
    Que el archivo existe.
    Que no tiene tamaño 0.
    Que el hash no está vacío.
'''

import os

def check_integridad_archivos(data_json):
    problemas = []

    clasificados = data_json.get("clasificados", {}).get("items", [])

    for item in clasificados:
        ruta = item.get("ruta")
        ubicacion = item.get("ubicacion")
        fecha = item.get("fecha")
        hash_archivo = item.get("hash")

        if not ruta or not os.path.exists(ruta):
            continue

        tam = os.path.getsize(ruta)
        if tam == 0:
            problemas.append({
                "tipo": "archivo_vacio",
                "ruta": ruta,
                "ubicacion": ubicacion + fecha,
                "mensaje": "El archivo tiene tamaño 0"
            })

        if not hash_archivo:
            problemas.append({
                "tipo": "hash_vacio",
                "ruta": ruta,
                "ubicacion": ubicacion + fecha,
                "mensaje": "El item no tiene hash definido"
            })

    return {
        "nombre": "Integridad básica de archivos",
        "problemas": problemas
    }
