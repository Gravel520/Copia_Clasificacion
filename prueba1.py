'''
Script en Python 
'''

import os
import subprocess

ruta_movil = '/sdcard/DCIM/Camera'

resultado = subprocess.run(['C:\\adb\\platform-tools\\adb', 'shell', f'ls {ruta_movil}'], capture_output=True, text=True)
archivos = resultado.stdout.strip().split('\n')
print(archivos)
print(len(archivos))

cj, ce, c4, otro = 0, 0, 0, 0
for archivo in archivos:
    if archivo.lower().endswith(('.jpg')):
        cj+=1
    elif archivo.lower().endswith(('.jpeg')):
        ce+=1
    elif archivo.lower().endswith(('.mp4')):
        c4+=1
    else:
        print(archivo)
        otro+=1

print(f'.jpg = {cj} - .jpeg = {ce} - .mp4 = {c4} - otro = {otro}')
