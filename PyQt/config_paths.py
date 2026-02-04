'''

'''

import os
from config_manager import settings
from geopy.geocoders import Nominatim

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

def get_spinner():
    return "./PyQt/assets/spinner.gif"

def get_ruta_mapa_html():
    return "./PyQt/mapas/mapa_fotos.html"

def get_ruta_ui():
    return "./PyQt/ui_files/MainWindow.ui"

def geocodificador():
    return Nominatim(user_agent="copilot-mapa")

def ruta_movil():
    return '/sdcard/DCIM/Camera'

def ruta_adb():
    return 'C:\\adb\\platform-tools\\adb'

def ruta_json_unico():
    return './archivos_unificados.json'

def meses():
    MESES = (
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
     'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    )
    return MESES
