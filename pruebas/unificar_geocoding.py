import json
import unicodedata

RUTA_UNIFICADO = './PyQt/archivos_json/archivos_unificados.json'
RUTA_CACHE_GEOCODING = './cache_geocoding.json'

def construir_cache_geocoding_desde_unificado():
    try:
        with open(RUTA_UNIFICADO, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("No se encontró archivos-Unificados.json")
        return {}
    except Exception as e:
        print("Error leyendo el archivo unificado:", e)
        return {}
    
    items = data.get("clasificados", {}).get("items", [])
    cache = {}

    for item in items:
        ubicacion_raw = item.get("ubicacion")
        lat = item.get("latitud")
        lon = item.get("longitud")

        if ubicacion_raw and lat is not None and lon is not None:

            ubicacion = normalizar_texto(ubicacion_raw)
            
            # Guardamos solo si no existe aún
            if ubicacion not in cache:
                cache[ubicacion] = [lat, lon]

    # Guardar cache
    with open(RUTA_CACHE_GEOCODING, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    print(f"Cache geocoding creado con {len(cache)} ubicaciones.")
    return cache

def normalizar_texto(t):
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))

def main():
    construir_cache_geocoding_desde_unificado()

if __name__ == '__main__':
    main()
