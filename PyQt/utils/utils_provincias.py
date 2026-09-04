'''
Script en PYthon.
'''

import requests
import time

# ============================================================
#  NORMALIZACIÓN DE NOMBRES
# ============================================================

def normalizar_provincia(nombre):
    if not nombre:
        return None
    
    nombre = nombre.strip()

    # Correcciones típicas de España
    reemplazos = {
        "Castilla-La Mancha": "Castilla La Mancha",
        "Castilla y León": "Castilla y Leon",
        "Comunidad de Madrid": "Madrid",
        "Galicia": "Galicia",
        "Andalucía": "Andalucia",
        "Principado de Asturias": "Asturias",
        "Comunidad Valenciana": "Valencia",
        "Cataluña": "Catalunya",
        "País Vasco": "Pais Vasco",
        "Comunidad Foral de Navarra": "Navarra",
        "Alacant / Alicante": "Alicante",
    }

    if nombre in reemplazos:
        return reemplazos[nombre]

    return nombre

# ============================================================
#  GEOCODING ROBUSTO
# ============================================================
def extraer_provincia_geocode_ciudad(ciudad, pais):
    """
    Devuelve lat, lon, provincia usando Nominatim con fallback robusto.
    """

    url = "https://nominatim.openstreetmap.org/search"

    country_map = {
        "es": "es",
        "españa": "es",
        "spain": "es",
        "pt": "pt",
        "portugal": "pt",
        "fr": "fr",
        "francia": "fr",
        "france": "fr"
    }


    params = {
        "city": ciudad,
        "countrycodes": country_map.get(pais.lower(), ""),
        "format": "json",
        "addressdetails": 1,
        "limit": 1
    }

    try:
        time.sleep(1)
        r = requests.get(
            url,
            params=params,
            headers={"User-Agent": "Copilot-Geocoder"},
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[ERROR] Geocoding falló para {ciudad}, {pais}: {e}")
        return None

    if not data:
        print(f"[WARN] Nominatim no encontró nada para: ({ciudad}, {pais})")
        return None
    
    addr = data[0].get("address", {})

    # ============================================================
    #  FALLBACKS ESPECÍFICOS POR PAÍS
    # ============================================================
    # Portugal
    if pais.lower() == "portugal":
        # Muchos pueblos devuelven solo municipality
        provincia = (
            addr.get("municipality")
            or addr.get("city")
        )

    # España
    elif pais.lower() == "españa":
        # Muchos pueblos devuelven sólo city/town
        provincia = (
            addr.get("province")
            or addr.get("county")
            or addr.get("state_district")
            or addr.get("municipality")
            or addr.get("city")
            or addr.get("town")
    )

    # Francia
    elif pais.lower() == "francia":
        provincia = (
            addr.get("country") 
            or addr.get("municipality")
            or addr.get("state")
        )

    # Azores / Madeira
    if not provincia and "state_district" in addr:
        provincia = addr["state_district"]

    # Último fallback
    if not provincia:
        print(f"[WARN] Geocoding falló para: ({ciudad}, {pais})")
        return None
    
    return normalizar_provincia(provincia)
