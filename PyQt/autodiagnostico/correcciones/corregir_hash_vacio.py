'''
Script en Python.
'''

import os

from copia_clasificador_fotos import actualizar_stats, calcular_hash_md5

def corregir_hash_vacio(lista_problemas, data):
    clasificados = data["clasificados"]["items"]
    eliminados = data["eliminados"]["items"]

    for p in lista_problemas:
        ruta = p.get("ruta")

        if not os.path.exists(ruta):
            continue

        nuevo_hash = calcular_hash_md5(ruta)

        if nuevo_hash is None:
            entrada = next((x for x in clasificados if x.get("ruta") == ruta), None)

            if os.path.exists(ruta):
                os.remove(ruta)

            clasificados[:] = [x for x in clasificados if x.get("ruta") != ruta]

            if entrada:
                eliminados.append({
                    "hash": entrada.get("hash")
                })

            continue

        entrada = next((x for x in clasificados if x.get("ruta") == ruta), None)

        if entrada:
            entrada["hash"] = nuevo_hash

    actualizar_stats(data)
    return data
