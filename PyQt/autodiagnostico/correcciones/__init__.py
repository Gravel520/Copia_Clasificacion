'''
Script en Python.
Se usa como router central dentro de DialogoAutodiagnostico.

Este archivo:
    · Importa todas las funciones de corrección.
    · Las registra en un diccionario CORRECCIONES.
    · Permite que tu diálogo llame simplemente:
        data = CORRECCIONES[tipo](lista_problemas, data)
'''

from .corregir_archivo_vacio import corregir_archivo_vacio
from .corregir_hash_vacio import corregir_hash_vacio
from .corregir_ruta_vacia import corregir_ruta_vacia
from . corregir_archivo_huerfano import corregir_archivo_huerfano
from .corregir_hash_duplicado import corregir_hash_duplicado
from .corregir_archivo_no_encontrado import corregir_archivo_no_encontrado
from .corregir_carpeta_incorrecta import corregir_carpeta_incorrecta
from .corregir_ubicacion_sin_cache import corregir_ubicacion_sin_cache

# Router de correcciones
CORRECCIONES = {
    "archivo_vacio": corregir_archivo_vacio,
    "hash_vacio": corregir_hash_vacio,
    "ruta_vacia": corregir_ruta_vacia,
    "archivo_huerfano": corregir_archivo_huerfano,
    "hash_duplicado": corregir_hash_duplicado,
    "archivo_no_encontrado": corregir_archivo_no_encontrado,
    "carpeta_incorrecta": corregir_carpeta_incorrecta,
    "ubicacion_sin_cache": corregir_ubicacion_sin_cache,
}
