'''
Script en Python.
Este módulo es equivalente a 'hash_indexer.py' pero usando ADB.
- Escanea carpetas del móvil.
- Descarga cada archivo temporalmente.
- Calcula su hash.
- Devuelve: 'hash -> ruta_adb'.
'''

import subprocess
import hashlib
import tempfile
import os

from typing import Dict, List

from config_paths import ruta_adb

def adb_listar_archivos(ruta_adb_movil: str) -> List[str]:
    '''
    Lista archivos en una ruta del móvil usando ADB.
    ruta_adb ejemplo: "adb://SERIAL/sdcard/DCIM"
    '''
    serial = ruta_adb_movil.split("adb://")[1].split("/")[0]

    partes = ruta_adb_movil.split("/")
    ruta_real = "/" + "/".join(partes[3:]) # Quiar el serial

    cmd = [ruta_adb(), "-s", serial, "shell", "ls", "-R", ruta_real]
    salida = subprocess.check_output(cmd, encoding="utf-8", errors="ignore")

    archivos = []
    for linea in salida.split("\n"):
        linea = linea.strip()
        if linea and not linea.endswith(":") and "." in linea:
            archivos.append(ruta_real + "/" + linea)

    return archivos

def adb_descargar_archivo(serial: str, ruta_remota: str) -> str:
    '''
    Descarga un archivo del móvil a un archivo temporal.
    Devuelve la ruta local temporal.
    '''
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.close()

    subprocess.call([ruta_adb(), "-s", serial, "pull", ruta_remota, tmp.name])

    return tmp.name

def calcular_hash_local(ruta: str, bloque: int = 1024 * 1024) -> str:
    md5 = hashlib.md5()
    with open(ruta, "rb") as f:
        while True:
            data = f.read(bloque)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def crear_indice_hashes_adb(rutas_adb: List[str]) -> Dict[str, List[str]]:
    '''
    Crea un índice hash -> rutas ADB.
    '''
    indice: Dict[str, List[str]] = {}

    for ruta_adb_movil in rutas_adb:
        serial = ruta_adb_movil.split("adb://")[1].split("/")[0]

        archivos = adb_listar_archivos(ruta_adb_movil)
        
        for ruta_remota in archivos:
            try:
                ruta_tmp = adb_descargar_archivo(serial, ruta_remota)
                h = calcular_hash_local(ruta_tmp)
                os.remove(ruta_tmp)

            except Exception:
                continue

            if h not in indice:
                indice[h] = []

            indice[h].append(f"{serial}:{ruta_remota}")
            
    return indice