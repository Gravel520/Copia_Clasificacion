'''
Script en Python.
Simula la restauración sin copiar archivos.
Devuelve:
    · faltantes: archivos que no existen en el PC
    · recuperables: archivos faltantes pero presentes en el índice
    · perdidos: archivos faltantes y NO presentes en el índice
    · carpetas_a_crear: carpetas que habría que crear
    · movimientos: rutas que cambiarían
'''

import os
from typing import Dict, List, Any

def simular_restauracion(data_json: Dict[str, Any],
                         indice_hashes: Dict[str, List[str]]) -> Dict[str, List[Any]]:
    resultado = {
        "faltantes": [],
        "recuperables": [],
        "perdidos": [],
        "carpetas_a_crear": [],
        "movimientos": []
    }

    items = data_json.get("clasificados", {}).get("items", [])

    for item in items:
        hash_archivo = item["hash"]
        ruta_destino = item["ruta"]

        # 1. ¿El archivo existe en el PC?
        if not os.path.exists(ruta_destino):
            resultado["faltantes"].append(ruta_destino)

            # 2. ¿Existe en alguna fuente externa?
            rutas_origen = indice_hashes.get(hash_archivo)

            if rutas_origen:
                resultado["recuperables"].append({
                    "hash": hash_archivo,
                    "ruta_destino": ruta_destino,
                    "ruta_origen": rutas_origen[0]
                })
            else:
                resultado["perdidos"].append({
                    "hash": hash_archivo,
                    "ruta_destino": ruta_destino
                })

        # 3. ¿La carpeta destino existe?
        carpeta = os.path.dirname(ruta_destino)
        if not os.path.exists(carpeta):
            resultado["carpetas_a_crear"].append(carpeta)

        # 4. ¿El archivo está en otra ruta del PC? (movido)
        if os.path.exists(ruta_destino):
            # Nada que hacer
            continue
        else:
            # Si el hash existe en el índice, pero la ruta destino no
            # existe -> movimiento
            if hash_archivo in indice_hashes:
                rutas_origen = indice_hashes[hash_archivo]
                for r in rutas_origen:
                    if os.path.exists(r):
                        if r != ruta_destino:
                            resultado["movimientos"].append({
                                "hash": hash_archivo,
                                "antes": r,
                                "despues": ruta_destino
                            })

    # Eliminar duplicados en carpetas
    resultado["carpetas_a_crear"] = list(set(resultado["carpetas_a_crear"]))

    return resultado
