'''

'''

import requests

# Cache interno para evitar peticiones repetidas
_cache_mapa = None
_cache_ciudades = {}

def obtener_paises_es():
    dic = mapa_es_en()
    return sorted(dic.keys())

def mapa_es_en():
    global _cache_mapa

    url = "https://restcountries.com/v3.1/all?fields=name"

    if _cache_mapa is not None:
        return _cache_mapa
    
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()

        dic = {}

        for p in data:
            nombre_en = p["name"]["common"]

            nombre_es = (
                p["name"]
                .get("nativeName", {})
                .get("spa", {})
                .get("common", nombre_en)
            )

            dic[nombre_es] = nombre_en
        
        _cache_mapa = dic
        return dic
    
    except Exception as e:
        print("Error creando mapa ES➡EN: ", e)
        return {}

def obtener_ciudades(pais_es):
    global _cache_ciudades

    # Si ya está en cache, devolverlo
    if pais_es in _cache_ciudades:
        return _cache_ciudades[pais_es]
    
    # Traducir país ES ➡ EN
    dic = mapa_es_en()
    pais_en = dic.get(pais_es)

    if not pais_en:
        return []
    
    url = "https://countriesnow.space/api/v0.1/countries"    

    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()

        for item in data["data"]:
            if item["country"].lower() == pais_en.lower():
                ciudades = item["cities"]
                _cache_ciudades[pais_es] = ciudades
                return ciudades
            
        return []
    
    except Exception as e:
        print("Error al obtener ciudades: ", e)
        return []
