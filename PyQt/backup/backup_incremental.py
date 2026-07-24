'''
Script en Python.
Este módulo compara dos estados del sistema (dos JSON) y genera un
archivo .diff.json con solo los cambios:

    · Archivos nuevos
    · Archivos modificados
    · Archivos eliminados
    · Archivos movidos
    · cambios en EXIF
    · cambios de ubicación/fecha
    · cambios en la ruta final
Este módulo compara:
· json_anterior
· json_actual

'''

import json
from typing import Dict, List, Any

def indexar_items(data_json: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    '''
    Convierte la lista de items en un índice:
    hash -> item
    '''
    items = data_json.get("clasificados", {}).get("items", [])
    return {item["hash"]: item for item in items}

def comparar_items(item_old: Dict[str, Any], item_new: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Compara dos items con el mismo hash y devuelve los campos que 
    han cambiado.
    '''
    cambios = {}

    for campo in ["ruta", "ubicacion", "fecha", "fecha_completa", "hora", "latitud", "longitud"]:
        if item_old.get(campo) != item_new.get(campo):
            cambios[campo] = {
                "antes": item_old.get(campo),
                "despues": item_new.get(campo)
            }
        
    return cambios

def generar_backup_incremental(json_anterior: Dict[str, Any],
                               json_actual: Dict[str, Any]) -> Dict[str, Any]:
    '''
    Genera un diff incremental entre dos JSON.
    '''

    old_index = indexar_items(json_anterior)
    new_index = indexar_items(json_actual)

    diff = {
        "nuevos": [],
        "eliminados": [],
        "modificados": [],
        "movidos": []
    }

    # 1. Detectar nuevos archivos.
    for h, item in new_index.items():
        if h not in old_index:
            diff["nuevos"].append(item)

    # 2. Detectar eliminados
    for h, item_new in new_index.items():
        if h in old_index:
            item_old = old_index[h]
            cambios = comparar_items(item_old, item_new)

            if cambios:
                # Si solo cambió la ruta -> es un movimiento.
                if list(cambios.keys()) == ["ruta"]:
                    diff["movidos"].append({
                        "hash": h,
                        "ruta_antes": cambios["ruta"]["antes"],
                        "ruta_despues": cambios["ruta"]["despues"]
                    })
                else:
                    diff["modificados"].append({
                        "hash": h,
                        "cambios": cambios
                    })

    return diff

def guardar_diff(diff: Dict[str, Any], ruta_salida: str):
    # Guarda el diff incremental en un archivo JSON.
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(diff, f, indent=4, ensure_ascii=False)

    print(f"Diff generado en {ruta_salida}")
    