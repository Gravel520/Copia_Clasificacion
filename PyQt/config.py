'''
Script en Python donde contenemos todas las variables absolutas,
y la configuración de la aplicación.
'''

from geopy.geocoders import Nominatim

# Variables para archivo 'mapa_generator.py'
RUTA_MAPAS = './PyQt/mapas/'
RUTA_PRINCIPAL = 'E:\\BackupFotos'
GEOCODIFICADOR = Nominatim(user_agent="copilot-mapa")
HISTORIAL = './duplicados.json'

# Variables para archivo 'copia_clasificador_fotos.py'
RUTA_MOVIL = '/sdcard/DCIM/Camera'
#RUTA_PC = 'C:\\Movil_Jesus_A33\\Camera'
RUTA_TEMPORAL = 'E:\\FotosTemp'
RUTA_ADB = 'C:\\adb\\platform-tools\\adb'
RUTA_ELIMINADOS = './eliminados.json'

# Variables para archivo 'main.py'
RUTA_MAPA_HTML = './PyQt/mapas/mapa_fotos.html'
RUTA_UI = './PyQt/ui_files/MainWindow.ui'
MESES = (
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
     'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
)
SPINNER = 'C:/Users/katal/Documents/Python/Copia_Clasificacion/PyQt/assets/spinner.gif'
SPINNER1 = 'C:/Users/katal/Documents/Python/Copia_Clasificacion/PyQt/assets/spinner1.gif'