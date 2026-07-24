'''
Script en Python.
Este módulo observa y registra todo lo que ocurre en tu sistema.
Es el equivalente a un "historial de eventos del backup", totalmente
determinista y compatible con tus otros módulos.
Es un registrador universal, que otros módulos pueden usar:
    · backup_restore.py -> registrar restauraciones.
    · backup_incremental.py -> registrar cambios.
    · backup_integritu.py -> registrar corrupción o inconsistencias.
    · autodiagnóstico.py -> registrar problemas detectados.
    · hash_indexer.py -> registrar cambios en el índice de hashes.
    
'''

import json
import time
from typing import Dict, Any

def timestamp():
    # Devuelve timestamp legible.
    return time.strftime("%Y-%m-%d %H:%M:%S")

def crear_evento(tipo: str, detalle: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Crea un evento de auditoría con:
    - tipo: "restaurado", "eliminado", "modificado", "movido", "error", etc..
    - detalle: información específica del evento.
    '''
    return {
        "timestamp": timestamp(),
        "tipo": tipo,
        "detalle": detalle
    }

def registrar_evento(audotoria: Dict[str, Any], evento: Dict[str, Any]):
    # Agrega un evento a la auditoría.
    audotoria["eventos"].append(evento)

def nueva_auditoria() -> Dict[str, Any]:
    # Crea la estructura inicial de auditoria.
    return {
        "eventos": []
    }

def guardar_auditoria(auditoria: Dict[str, Any], ruta_archivo: str):
    # Guarda la auditoría en un archivo JSON.
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        json.dump(auditoria, f, indent=4, ensure_ascii=False)

    print(f"Auditoría guardada en {ruta_archivo}")
