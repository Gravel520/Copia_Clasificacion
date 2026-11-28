'''
Script en Python.
'''

import os
import shutil

def copiar_carpeta_cancelable(origen, destino, cancelado_callback=None, archivo_callback=None):
    os.makedirs(destino, exist_ok=True)

    for root, dirs, files in os.walk(origen):
        if cancelado_callback and cancelado_callback():
            raise InterruptedError()
        
        relativo = os.path.relpath(root, origen)

        destino_actual = os.path.join(destino, relativo)

        os.makedirs(destino_actual, exist_ok=True)

        for archivo in files:
            if cancelado_callback and cancelado_callback():
                raise InterruptedError()
            
            origen_archivo = os.path.join(root, archivo)

            destino_archivo = os.path.join(destino_actual, archivo)

            shutil.copy2(origen_archivo, destino_archivo)
            
            if archivo_callback:
                archivo_callback(origen_archivo)
    
def formatear_segundos(segundos):
    segundos = max(0, int(segundos))
    horas = segundos // 3600

    minutos = (segundos % 3600) // 60
    segundos = segundos % 60

    if horas:
        return (f"{horas:02d}:{minutos:02d}:{segundos:02d}")
    
    return (f"{minutos:02d}:{segundos:02d}")
