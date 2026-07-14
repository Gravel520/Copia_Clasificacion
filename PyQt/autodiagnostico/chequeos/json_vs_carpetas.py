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

    # Archivos del JSON  que no existen o están mal ubicados
    rutas_json = set()

    for item in clasificados:
        hash = item.get("hash")
        ruta = item.get("ruta")
        ubicacion = item.get("ubicacion")
        fecha = item.get("fecha")

        if not ruta:
            problemas.append({
                "tipo": "ruta_vacia",
                "hash": hash,
                "detalle": ubicacion + fecha,
                "ubicacion": ubicacion,
                "fecha": fecha,
                "mensaje": "Item sin ruta definida"
            })
            continue

        rutas_json.add(os.path.normpath(ruta))

        if not os.path.exists(ruta):
            problemas.append({
                "tipo": "archivo_no_encontrado",
                "ruta": ruta,
                "ubicacion": ubicacion + fecha,
                "detalle": ubicacion + fecha,
                "mensaje": "El archivo no existe en disco"
            })
            continue

    # Archivos en disco que NO están en el JSON
    rutas_fisicas = set()

    for carpeta in os.listdir(raiz_backup):
        ruta_carpeta = os.path.join(raiz_backup, carpeta)
        if not os.path.isdir(ruta_carpeta):
            continue

        for archivo in os.listdir(ruta_carpeta):
            ruta_archivo = os.path.normpath(os.path.join(ruta_carpeta, archivo))

            if os.path.isfile(ruta_archivo):
                rutas_fisicas.add(ruta_archivo)
    
    # Diferencia: archivos en disco que no están en JSON
    archivos_huerfanos = rutas_fisicas - rutas_json

    for ruta in archivos_huerfanos:
        problemas.append({
            "tipo": "archivo_huerfano",
            "ruta": "(" + ruta.split("(", 1)[1],
            "detalle": "(" + ruta.split("(", 1)[1],
            "mensaje": "Archivo existe en disco pero no está registrado en el JSON"
        })

    # Duplicados por hash
    hashes = {}
    for item in clasificados:
        h = item.get("hash")
        if not h:
            continue
        if h not in hashes:
            hashes[h] = []
        hashes[h].append(item)

    for h, items in hashes.items():
        if len(items) > 1:
            ruta = [i["ruta"] for i in items]
            ubic = [i["ubicacion"] + i["fecha"] for i in items]
            problemas.append({
                "tipo": "hash_duplicado",
                "hash": h,
                "ruta": ruta,
                "ubicacion": ubic[0],
                "detalle": ubic[0],
                "mensaje": "Hash duplicado en el JSON"
            })

    return {
        "nombre": "JSON vs Carpetas",
        "problemas": problemas
    }
