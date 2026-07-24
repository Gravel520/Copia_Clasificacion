'''
Script en Python.
Este módulo implementa la restauración determinista:
si un archivo falta en el PC, se busca por hash en el índice y se
reconstruye exactamente en la ruta que aparece en el .json.

'''

import os
import shutil
from typing import Dict, List, Any

def asegurar_carpeta(ruta_archivo: str):
    # Crea la carpeta destino si no existe.
    carpeta = os.path.dirname(ruta_archivo)
    os.makedirs(carpeta, exist_ok=True)

def restaurar_archivo(hash_objetivo: str,
                      ruta_destino: str,
                      indice_hashes: Dict[str, List[str]],
                      resultado: Dict[str, List[str]]) -> bool:
    '''
    Intenta restaurar un archivo:
    - Si ya existe -> no hace nada.
    - Si no existe -> buscar por hash en el índice y lo copia.
    Devuelve True si se restauro, False si no.
    '''

    # 1. Si ya existe, no hay nada que restaurar.
    if os.path.exists(ruta_destino):
        resultado["ya_clasificados"].append(ruta_destino)
        return False
    
    # 2. Buscar por hash en el índice.
    rutas_origen = indice_hashes.get(hash_objetivo, [])
    if not rutas_origen:
        return False
    
    rutas_origen = rutas_origen[0]

    # 3. Crear carpeta destino si falta
    asegurar_carpeta(ruta_destino)

    # 4. Copiar el primero que encuentre.
    try:
        shutil.copy2(rutas_origen, ruta_destino)
        return True
    except Exception:
        return False
    
def restaurar_desde_json(data_json: Dict[str, Any],
                         indice_hashes: Dict[str, List[str]]) -> Dict[str, List[str]]:
    '''
    Recorre todo el JSON y restaura archivos faltantes.
    Devuelve un dict con:
    - restaurados: ruta restauradas
    - no_encontrados: hashes sin archivo origen
    - errores: rutas que no pudieron copiarse
    '''

    resultado = {
        "restaurados": [],
        "no_encontrados": [],
        "errores": [],
        "ya_clasificados": []
    }

    items = data_json.get("clasificados", {}).get("items", [])

    for item in items:
        hash_archivo = item["hash"]
        ruta_destino = item["ruta"]

        # Intentar restaurar
        ok = restaurar_archivo(hash_archivo, ruta_destino, indice_hashes, resultado)

        if ok:
            resultado["restaurados"].append(ruta_destino)
        else:
            # Si no existe en índice -> archivo perdido
            if hash_archivo not in indice_hashes:
                resultado["no_encontrados"].append(hash_archivo)
            # Si existe pero no se pudo copiar -> error
            else:
                resultado["errores"].append(ruta_destino)

    return resultado
