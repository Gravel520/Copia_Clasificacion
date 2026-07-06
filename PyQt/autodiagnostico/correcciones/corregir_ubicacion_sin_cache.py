'''
Script en Python.
'''

from copia_clasificador_fotos import cargar_cache, guardar_cache

def añadir_ubicacion_al_cache(ubic, data, cache):
    clasificados = data["clasificados"]["items"]
    ubicacion = next((x for x in clasificados if x["ubicacion"] == ubic), None)

    if ubicacion is None:
        return cache

    lat = ubicacion.get("latitud", 0)
    lon = ubicacion.get("longitud", 0)

    # Añadir al cache
    cache[ubic] = [lat, lon]

    return cache

def corregir_ubicacion_sin_cache(lista_problemas, data):
    cache = cargar_cache()

    for p in lista_problemas:
        ubic = p.get("ubicacion")

        cache = añadir_ubicacion_al_cache(ubic, data, cache)

    guardar_cache(cache)

    return data
