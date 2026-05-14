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

def get_ruta_mapa_html():
    return "./PyQt/mapas/mapa_fotos.html"

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
    