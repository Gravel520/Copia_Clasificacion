'''
Script en Python.
'''

from copia_clasificador_fotos import actualizar_stats
from autodiagnostico.utils.deshabilitar_mapa import set_deshabilitar_mapa

def corregir_archivo_no_encontrado(lista_problemas, data):
    clasificados = data.get("clasificados", {}).get("items", [])
    eliminados = data.get("eliminados", {}).get("items", [])

    for p in lista_problemas:
        ruta = p.get("ruta")

        for item in list(clasificados):
            if item.get("ruta") == ruta:
                clasificados.remove(item)
                eliminados.append({
                    "hash": item.get("hash")
                })
    
    if "stats" not in data:
        data["stats"] = {
            "total_clasificados": 0,
            "total_eliminados": 0,
        }

    actualizar_stats(data)
    
    set_deshabilitar_mapa()
    return data
