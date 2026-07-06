'''
Script en Python.
'''

import os

from copia_clasificador_fotos import actualizar_stats

def corregir_archivo_vacio(lista_problemas, data):
    clasificados = data["clasificados"]["items"]
    eliminados = data["eliminados"]["items"]

    for p in lista_problemas:
        ruta = p.get("ruta")

        entrada = next((x for x in clasificados if x.get("ruta") == ruta), None)

        if os.path.exists(ruta):
            os.remove(ruta)

        clasificados[:] = [x for x in clasificados if x.get("ruta") != ruta]

        if entrada:
            eliminados.append({
                "hash": entrada.get("hash")
            })

    actualizar_stats(data)
    return data
