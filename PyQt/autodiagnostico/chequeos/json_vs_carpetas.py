'''
Script en Python.

Validamos que:
    La ruta existen en disco.
    La carpeta donde está el archivo coincide con ubicacion + fecha.
'''

import os

def extraer_carpeta_de_ruta(ruta):
    carpeta = os.path.dirname(ruta)
    return os.path.basename(carpeta)

def construir_nombre_carpeta(ubicacion, fecha):
    return f"{ubicacion}{fecha}"

def check_json_vs_carpetas(data_json, raiz_backup):
    problemas = []

    clasificados = data_json.get("clasificados", {}).get("items", [])

    for item in clasificados:
        ruta = item.get("ruta")
        ubicacion = item.get("ubicacion")
        fecha = item.get("fecha")

        if not ruta:
            problemas.append({
                "tipo": "ruta_vacia",
                "item": item,
                "mensaje": "Item sin ruta definida"
            })
            continue

        if not os.path.exists(ruta):
            problemas.append({
                "tipo": "archivo_no_encontrado",
                "ruta": ruta,
                "mensaje": "El archivo no existe en disco"
            })
            continue

        carpeta_real = extraer_carpeta_de_ruta(ruta)
        carpeta_esperada = construir_nombre_carpeta(ubicacion, fecha)

        if carpeta_real != carpeta_esperada:
            problemas.append({
                "tipo": "carpeta_incorrecta",
                "ruta": ruta,
                "carpeta_real": carpeta_real,
                "carpeta_esperada": carpeta_esperada
            })

    return {
        "nombre": "JSON vs Carpetas",
        "problemas": problemas
    }
