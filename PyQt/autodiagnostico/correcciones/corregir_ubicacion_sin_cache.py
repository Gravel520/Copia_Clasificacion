'''
Script en Python.
'''

from copia_clasificador_fotos import cargar_cache, guardar_cache

def añadir_ubicacion_al_cache(clave, data, cache):
    clasificados = data["clasificados"]["items"]
    ubicacion = next((x for x in clasificados if x["ubicacion"] == clave), None)

    if ubicacion is None:
        return cache

    lat = ubicacion.get("latitud", 0)
    lon = ubicacion.get("longitud", 0)

    # Añadir al cache
    # Si ya existe entrada en formato nuevo, conservar provincia/postal
    if clave in cache and isinstance(cache[clave], dict):
        provincia = cache[clave].get("provincia", "")
        postal = cache[clave].get("postal", "")
        ciudad = cache[clave].get("ciudad", "")
        pais = cache[clave].get("pais", "")
    else:
        # Extraer ciudad y país desde la clave "(ciudad)(pais)"
        try:
            ciudad = clave.split(')')[0][1:]
            pais = clave.split(')')[1][1:]
        except:
            ciudad = ""
            pais = ""

        provincia = ""
        postal = ""

    # Guardar en formato nuevo
    cache[clave] = {
        "lat": float(lat),
        "lon": float(lon),
        "ciudad": ciudad,
        "pais": pais,
        "provincia": provincia,
        "postal": postal,
        "fuente": "correccion"
    }

    return cache

def corregir_ubicacion_sin_cache(lista_problemas, data):
    cache = cargar_cache()

    for p in lista_problemas:
        ubic = p.get("ubicacion")

        cache = añadir_ubicacion_al_cache(ubic, data, cache)

    guardar_cache(cache)

    return data
