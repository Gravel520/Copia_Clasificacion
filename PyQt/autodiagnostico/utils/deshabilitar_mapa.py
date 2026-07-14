'''
Script en Python.

Con este código modificamos el archivo de configuración para
deshabilitar el mapa y tener que generarlo de nuevo de forma
manual.
'''

import config_manager

def set_deshabilitar_mapa():
    config_manager.settings.setValue("Estado/mapa_generado", "False")
    config_manager.settings.sync()
