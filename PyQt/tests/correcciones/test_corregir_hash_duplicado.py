from autodiagnostico.correcciones.corregir_hash_duplicado import corregir_hash_duplicado

def test_corregir_hash_duplicado():
    data = {
        "clasificados": {"items": [
            {"hash": "hash1", "ruta": "ruta1", "ubicacion": "ubicacion1", "latitud": 1, "longitud": 1},
            {"hash": "hash1", "ruta": "ruta2", "ubicacion": "ubicacion2", "latitud": 2, "longitud": 2},
            {"hash": "hash2", "ruta": "ruta3", "ubicacion": "ubicacion3", "latitud": 3, "longitud": 3},
            {"hash": "hash3", "ruta": "ruta4", "ubicacion": "ubicacion4", "latitud": 4, "longitud": 4},
            {"hash": "hash4", "ruta": "ruta5", "ubicacion": "ubicacion5", "latitud": 5, "longitud": 5}
        ]}
    }

    problemas = [{"hash": "hash1", "tipo": "hash_duplicado"}]

    data = corregir_hash_duplicado(problemas, data)

    items = data["clasificados"]["items"]

    assert len([i for i in items if i["hash"] == "hash1"]) == 1
    assert len([i for i in items if i["hash"] == "hash2"]) == 1
    assert len([i for i in items if i["hash"] == "hash3"]) == 1
    assert len([i for i in items if i["hash"] == "hash4"]) == 1
    