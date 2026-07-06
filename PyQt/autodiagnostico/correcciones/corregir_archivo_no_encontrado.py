'''
Script en Python.
'''

from copia_clasificador_fotos import actualizar_stats

def corregir_archivo_no_encontrado(lista_problemas, data):
    clasificados = data["clasificados"]["items"]

    for p in lista_problemas:
        ruta = p.get("ruta")

        clasificados[:] = [x for x in clasificados if x.get("ruta") != ruta]

    actualizar_stats(data)
    return data
