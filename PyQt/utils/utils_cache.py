import json
import re
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
    if not t or not isinstance(t, str):
        return ""
    
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    # Quedarnos solamente con números, letras y espacios.
    t = re.sub(r'[^a-zA-Z0-9 ]', '', t)
    return t