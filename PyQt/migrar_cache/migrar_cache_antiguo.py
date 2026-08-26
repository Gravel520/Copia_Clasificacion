'''

'''
import sys
import os

# Añadir la raíz del proyecto al sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, BASE_DIR)

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

PROVINCIAS_ES = {
    "01": "Vitoria", "02": "Albacete", "03": "Alicante", "04": "Almería",
    "05": "Ávila", "06": "Badajoz", "07": "Baleares", "08": "Barcelona",
    "09": "Burgos", "10": "Cáceres", "11": "Cádiz", "12": "Castellón",
    "13": "Ciudad Real", "14": "Córdoba", "15": "A Coruña", "16": "Cuenca",
    "17": "Girona", "18": "Granada", "19": "Guadalajara", "20": "San Sebastian",
    "21": "Huelva", "22": "Huesca", "23": "Jaén", "24": "León",
    "25": "Lleida", "26": "La Rioja", "27": "Lugo", "28": "Madrid",
    "29": "Málaga", "30": "Murcia", "31": "Pamplona", "32": "Ourense",
    "33": "Oviedo", "34": "Palencia", "35": "Las Palmas", "36": "Pontevedra",
    "37": "Salamanca", "38": "Santa Cruz de Tenerife", "39": "Santander",
    "40": "Segovia", "41": "Sevilla", "42": "Soria", "43": "Tarragona",
    "44": "Teruel", "45": "Toledo", "46": "Valencia", "47": "Valladolid",
    "48": "Bilbao", "49": "Zamora", "50": "Zaragoza", "51": "Ceuta",
    "52": "Melilla"
}
PROVINCIAS_PT = {
    "1": "Lisboa", 
    "2": "Santarém",
    "3": "Setúbal", 
    "4": "Évora", 
    "5": "Beja", 
    "6": "Faro",
    "7": "Portalegre",
    "8": "Castelo Branco",
    "9": "Azores Madeira", 
}
PROVINCIAS_FR = {
    "01": "Ain", "02": "Aisne", "03": "Allier", "04": "Alpes-de-Haute-Provence",
    "05": "Hautes-Alpes", "06": "Alpes-Maritimes", "07": "Ardèche", "08": "Ardennes",
    "09": "Ariège", "10": "Aube", "11": "Aude", "12": "Aveyron",
    "13": "Bouches-du-Rhône", "14": "Calvados", "15": "Cantal", "16": "Charente",
    "17": "Charente-Maritime", "18": "Cher", "19": "Corrèze", "21": "Côte-d'Or",
    "22": "Côtes-d'Armor", "23": "Creuse", "24": "Dordogne", "25": "Doubs",
    "26": "Drôme", "27": "Eure", "28": "Eure-et-Loir", "29": "Finistère",
    "30": "Gard", "31": "Haute-Garonne", "32": "Gers", "33": "Gironde",
    "34": "Hérault", "35": "Ille-et-Vilaine", "36": "Indre", "37": "Indre-et-Loire",
    "38": "Isère", "39": "Jura", "40": "Landes", "41": "Loir-et-Cher",
    "42": "Loire", "43": "Haute-Loire", "44": "Loire-Atlantique", "45": "Loiret",
    "46": "Lot", "47": "Lot-et-Garonne", "48": "Lozère", "49": "Maine-et-Loire",
    "50": "Manche", "51": "Marne", "52": "Haute-Marne", "53": "Mayenne",
    "54": "Meurthe-et-Moselle", "55": "Meuse", "56": "Morbihan", "57": "Moselle",
    "58": "Nièvre", "59": "Nord", "60": "Oise", "61": "Orne",
    "62": "Pas-de-Calais", "63": "Puy-de-Dôme", "64": "Pyrénées-Atlantiques",
    "65": "Hautes-Pyrénées", "66": "Pyrénées-Orientales", "67": "Bas-Rhin",
    "68": "Haut-Rhin", "69": "Rhône", "70": "Haute-Saône", "71": "Saône-et-Loire",
    "72": "Sarthe", "73": "Savoie", "74": "Haute-Savoie", "75": "Paris",
    "76": "Seine-Maritime", "77": "Seine-et-Marne", "78": "Yvelines",
    "79": "Deux-Sèvres", "80": "Somme", "81": "Tarn", "82": "Tarn-et-Garonne",
    "83": "Var", "84": "Vaucluse", "85": "Vendée", "86": "Vienne",
    "87": "Haute-Vienne", "88": "Vosges", "89": "Yonne", "90": "Territoire de Belfort",
    "91": "Essonne", "92": "Hauts-de-Seine", "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne", "95": "Val-d'Oise"
}


def migrar_cache_geocoding():
    cache = cargar_cache()
    if not isinstance(cache, dict):
        print("[ERROR] Cache geocoding corrupto o vacío.")
        return
    
    geolocator = Nominatim(user_agent="migracion_cache")
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)

    cambios = 0

    for clave, valor in list(cache.items()):

        # 1. Saltar entradas Sin_GPS
        if clave == "(Sin_GPS)":
            continue

        # 2. Si ya está en formato nuevo -> saltar
        if isinstance(valor, dict) and "lat" in valor and "lon" in valor:
            continue

        # 3. Si es formato antiguo -> migrar
        if isinstance(valor, list) and len(valor) == 2:
            lat, lon = valor

            # Extraer ciudad y país desde la clave "(ciudad)(país)"
            try:
                ciudad = clave.split(')')[0][1:]
                pais = clave.split(')')[1][1:]
            except Exception:
                print(f"[WARN] Clave mal formada: {clave}")
                continue

            ciudad_norm = normalizar_texto(ciudad)
            pais_norm = normalizar_texto(pais)

            # 4. Intentar obtener provincia y postal
            provincia = ""
            postal = ""

            try:
                ubicacion = reverse((lat, lon), language="es")
                if ubicacion:
                    datos = ubicacion.raw.get("address", {})
                    postal = datos.get("postcode", "")
                    provincia = obtener_provincia_por_postal(postal, pais_norm)

            except Exception as e:
                print(f"[WARN] Reverse geocoding fallo para {clave}: {e}")

            # 5. Crear entrada nueva
            cache[clave] = {
                "lat": float(lat),
                "lon": float(lon),
                "ciudad": ciudad_norm,
                "pais": pais_norm,
                "provincia": provincia,
                "postal": postal,
                "fuente": "migracion"
            }

            cambios += 1
            print(cambios, clave, provincia, postal)

    guardar_cache(cache)
    print(f"[INFO] Se migraron {cambios} entradas del cache geocoding.")

import json
import unicodedata
ruta_cache_json_geocoding = "./PyQt/archivos_json/cache_geocoding.json"

def cargar_cache():
    try:
        with open(ruta_cache_json_geocoding, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def guardar_cache(cache):
    with open(ruta_cache_json_geocoding, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def normalizar_texto(t):
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))

def obtener_provincia_por_postal(postal, pais):
    if not postal or len(postal) < 2:
        return ""
    
    prefijo = postal[:2]

    if pais == "Espana":
        return PROVINCIAS_ES.get(prefijo, "")
    elif pais == "Portugal":
        prefijo = postal[:1]
        return PROVINCIAS_PT.get(prefijo, "")
    elif pais == "Francia":
        return PROVINCIAS_FR.get(prefijo, "")
    else:
        return ""
    
migrar_cache_geocoding()