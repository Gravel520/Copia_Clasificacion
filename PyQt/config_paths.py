'''

'''

import os
from pathlib import Path
from config_manager import settings
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def get_unidad():
    return settings.value("General/unidad", "")

def get_ruta_principal():
    destino = settings.value("Paths/destino", "")
    if not destino:
        return ""
    destino = destino.replace("/", "\\\\")
    return os.path.join(destino, "BackupFotos")

def get_ruta_backup():
    return "./PyQt/"

def get_ruta_temporal():
    unidad = get_unidad()
    return f"{unidad}FotosTemp"

def get_ruta_miniaturas():
    unidad = Path(get_unidad())
    return unidad / "Miniaturas"

def get_spinner():
    return "./PyQt/assets/spinner.gif"

def get_assets():
    return "./PyQt/assets/"

def get_ruta_mapa_fotos_html():
    return "./PyQt/mapas/mapa_fotos.html"

def get_ruta_mapa_grupos_html():
    return "./PyQt/mapas/mapa_grupos.html"

def get_ruta_mapa_provincias_html():
    return "./PyQt/mapas/mapa_provincias.html"

def get_enviando():
    return "./PyQt/compartir/assets/enviar.gif"

def get_ruta_logo():
    return "./PyQt/assets/Logo.png"

def get_ruta_ui():
    return "./PyQt/ui_files/MainWindow.ui"

def geocodificador():
    geolocator = Nominatim(user_agent="copilot-mapa")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1)
    return geocode, reverse

def ruta_movil():
    return '/sdcard/DCIM/Camera'

def ruta_adb():
    return 'C:\\adb\\platform-tools\\adb.exe'

def ruta_json_unico():
    return './PyQt/archivos_json/archivos_unificados.json'

def ruta_json_miniaturas():
    return Path('./PyQt/archivos_json/miniaturas.json')

def ruta_cache_json_geocoding():
    return Path("./PyQt/archivos_json/cache_geocoding.json")

def ruta_json_grupos():
    return Path("./PyQt/archivos_json/grupos.json")

def ruta_exiftools():
    return 'C:\exiftool\exiftool.exe'

def meses():
    return (
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
     'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    )

def extensiones_validas(tipo="todas"):
    EXTENSIONES_IMAGEN = (
        ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", 
        ".tif", ".ppm", ".pgm", ".pbm", ".pnm", ".tga", ".svg"
    )

    EXTENSIONES_VIDEO = (
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".mpeg", ".mpg", ".m4v", ".3gp", ".mts", ".m2ts", ".ts", ".ogv"
    )

    if tipo == "imagen":
        return EXTENSIONES_IMAGEN
    elif tipo == "video":
        return EXTENSIONES_VIDEO
    else:
        # Devuelve ambas juntas
        return EXTENSIONES_IMAGEN + EXTENSIONES_VIDEO
    
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