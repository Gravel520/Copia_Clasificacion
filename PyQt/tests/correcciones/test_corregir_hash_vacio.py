import os
from autodiagnostico.correcciones.corregir_hash_vacio import corregir_hash_vacio

def test_corregir_hash_vacio(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"hola") # Archivo vacío

    data = {
        "clasificados": {"items": [
            {"ruta": str(ruta), "hash": ""}
        ]},
        "eliminados": {"items": []}
    }

    problemas = [{"ruta": str(ruta), "tipo": "hash_vacio"}]

    data = corregir_hash_vacio(problemas, data)

    entrada = data["clasificados"]["items"][0]
    assert len(entrada["hash"]) > 0 # hash recalculado
    