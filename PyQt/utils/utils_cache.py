import json
import unicodedata
from config_paths import ruta_cache_json_geocoding

def cargar_cache():
    try:
        with open(ruta_cache_json_geocoding(), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_cache(cache):
    with open(ruta_cache_json_geocoding(), "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def normalizar_texto(t):
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))

