import json

def migrar_json(clasificados_path, pendientes_path, eliminados_path, salida_path):
    with open(clasificados_path, 'r', encoding='utf-8') as f:
        clasificados = json.load(f)

    with open(pendientes_path, 'r', encoding='utf-8') as f:
        pendientes = json.load(f)

    with open(eliminados_path, 'r', encoding='utf-8') as f:
        eliminados = json.load(f)

    data_unificada = {
        "version": 1,
        "clasificados": {"items": clasificados},
        "pendientes": {"items": pendientes},
        "eliminados": {"items": eliminados},
        "stats": {
            "total_clasificados": len(clasificados),
            "total_pendientes": len(pendientes),
            "total_eliminados": len(eliminados)
        }
    }

    with open(salida_path, 'w', encoding='utf-8') as f:
        json.dump(data_unificada, f, indent=4, ensure_ascii=False)

    print("Migración completada.")

migrar_json(
    "clasificados.json",
    "pendientes.json",
    "eliminados.json",
    "archivos_unificados.json"
)