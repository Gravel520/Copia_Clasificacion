'''
Script en Python donde contenemos todas las variables absolutas,
y la configuración de la aplicación.
'''

from geopy.geocoders import Nominatim
from config_manager import settings

UNIDAD = settings.value("General/unidad")

# Variables para archivo 'mapa_generator.py'
RUTA_MAPAS = './PyQt/mapas/'

ruta = settings.value("Paths/destino").replace("/", "\\\\")
RUTA_PRINCIPAL = f'{ruta}\\\\BackupFotos'

#GEOCODIFICADOR = Nominatim(user_agent="copilot-mapa")

# Variables para archivo 'copia_clasificador_fotos.py'
RUTA_MOVIL = '/sdcard/DCIM/Camera'
RUTA_TEMPORAL = F'{UNIDAD}FotosTemp'
RUTA_ADB = 'C:\\adb\\platform-tools\\adb'
RUTA_JSON_UNICO = './archivos_unificados.json'

# Variables para archivo 'main.py'
RUTA_MAPA_HTML = './PyQt/mapas/mapa_fotos.html'
RUTA_UI = './PyQt/ui_files/MainWindow.ui'
MESES = (
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
     'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
)
SPINNER = 'C:/Users/katal/Documents/Python/Copia_Clasificacion/PyQt/assets/spinner.gif'
SPINNER1 = 'C:/Users/katal/Documents/Python/Copia_Clasificacion/PyQt/assets/spinner1.gif'

API_KEY_COINTRY = '4757B8F2-09DA-4DE2-B5A3-5789FB318288'
