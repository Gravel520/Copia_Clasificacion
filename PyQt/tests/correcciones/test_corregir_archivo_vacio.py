import os
from autodiagnostico.correcciones.corregir_archivo_vacio import corregir_archivo_vacio

def test_corregir_archivo_vacio(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"") # Archivo vacío

    data = {
        "clasificados": {"items": [
            {"ruta": str(ruta), "hash": "abc123"}
        ]},
        "eliminados": {"items": []}
    }

    problemas = [{"ruta": str(ruta), "tipo": "archivo_vacio"}]

    data = corregir_archivo_vacio(problemas, data)

    assert not ruta.exists()
    assert len(data["clasificados"]["items"]) == 0
    assert data["eliminados"]["items"][0]["hash"] == "abc123"
