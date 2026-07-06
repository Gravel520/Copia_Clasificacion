'''
Script en Python.
'''

from copia_clasificador_fotos import actualizar_stats

def corregir_hash_duplicado(lista_problemas, data):
    clasificados = data["clasificados"]["items"]

    for p in lista_problemas:
        hash_buscado = p.get("hash")

        entradas = [x for x in clasificados if x.get("hash") == hash_buscado]

        if len(entradas) > 1:
            entrada_valida = entradas[0]
            for entrada in entradas[1:]:
                clasificados.remove(entrada)

    actualizar_stats(data)
    return data
