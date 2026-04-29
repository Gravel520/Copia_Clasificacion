'''

'''

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
    
print(copia_binaria_fuerza("20260414_143814.jpg", "C:"))