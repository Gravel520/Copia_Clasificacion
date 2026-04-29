'''
Instalar la libreria hachoir.
'''

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
import subprocess
ruta_adb = 'C:\\adb\\platform-tools\\adb.exe'
ruta_movil = '/sdcard/DCIM/Camera'

def copia_binaria_fuerza(archivo, ruta_local):
    ruta_origen = f"{ruta_movil}/{archivo}"
    print(ruta_origen)

    comando = f'"{ruta_adb}" shell cat {ruta_origen} > "{ruta_local}"'

    try:
        subprocess.run(comando, shell=True, check=True)
        return True
    except:
        return False
    
print(copia_binaria_fuerza("20251230_211515.jpg", "C:"))

def obtener_gps_video(ruta_archivo):
    parser = createParser(ruta_archivo)
    with parser:
        metadata = extractMetadata(parser)
        if metadata:
            return metadata
    return None

print(obtener_gps_video("C:\BackupFotos\(Fuenlabrada)(Espana)(2025-12)/20251230_211515.jpg"))
