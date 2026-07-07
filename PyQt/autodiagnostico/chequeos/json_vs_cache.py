'''
Scrip en Python.
Queremos ver:
    Ubicaciones usadas en clasificados que no están en el cache.
    Ubicaciones en el cache que no se usan en ningún clasificado (esto
    es más informativo).
'''

def check_json_vs_cache(data_json, cache_ubicaciones):
    problemas = []

    clasificados = data_json.get("clasificados", {}).get("items", [])

    # Detectar hash vacío
    for item in clasificados:
        if item.get("hash", "") == "":
            problemas.append({
                "tipo": "hash_vacio",
                "ruta": item.get("ruta"),
                "mensaje": "El hash está vacio."
            })

    # Ubicaciones usadas
    ubicaciones_usadas = set(
        item.get("ubicacion")
        for item in clasificados
        if item.get("ubicacion")
    )

    ubicaciones_cache = set(cache_ubicaciones.keys())

    # Ubicaciones usadas pero no presentes en cache
    faltan_en_cache = ubicaciones_usadas - ubicaciones_cache
    for ubic in faltan_en_cache:
        problemas.append({
            "tipo": "ubiacion_sin_cache",
            "ubicacion": ubic,
            "mensaje": "Ubicación usada en clasificados pero no presente en cache."
        })

    return {
        "nombre": "JSON vs Cache de ubicaciones",
        "problemas": problemas
    }
