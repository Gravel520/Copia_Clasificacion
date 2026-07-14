'''
Script en Python.
'''

import os

def corregir_directorio_vacio(lista_problemas, data):
    """
    Ellimina del disco las carpetas que no contienen archivos.
    No modifica el JSON porque los directorios vacíos no afectan
        a 'clasificados.json'.
    """
    for p in lista_problemas:
        ruta_carpeta = p.get("ruta")

        # Seguridad: si no existe, no hacemos nada
        if not ruta_carpeta or not os.path.isdir(ruta_carpeta):
            continue

        try:
            # Eliminar carpeta vacía
            os.rmdir(ruta_carpeta)
        except OSError:
            # Si no está vacía o no se puede borrar, ignoramos
            pass

    return data