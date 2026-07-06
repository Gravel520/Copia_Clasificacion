import os
from autodiagnostico.correcciones.corregir_ruta_vacia import corregir_ruta_vacia

def test_corregir_ruta_vacia(tmp_path):
    carpeta = tmp_path / "(Madrid)(Espana)(2024-05)"
    carpeta.mkdir()

    ruta = carpeta / "foto.jpg"
    ruta.write_bytes(b"hola") 

    data = {
        "clasificados": {"items": [
            {"hash": "abc123", "ruta": "", "ubicacion": "(Madrid)(Espana)", "fecha": "(2024-05)"}
        ]},
        "eliminados": {"items": []}
    }
    
    problemas = [{
        "tipo": "ruta_vacia",
        "hash": "abc123",
        "ubicacion": "(Madrid)(Espana)",
        "fecha": "(2024-05)"
    }]

    data = corregir_ruta_vacia(problemas, data)

    entrada = data["clasificados"]["items"][0]
    assert entrada["ruta"].endswith("foto.jpg")
    