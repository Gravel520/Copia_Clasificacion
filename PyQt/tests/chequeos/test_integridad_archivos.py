import os
from autodiagnostico.chequeos.integridad_archivos import check_integridad_archivos

def test_integridad_archivos_archivo_vacio(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"") # Archivo vacío

    data = {
        "clasificados": {"items": [
            {"ruta": str(ruta), "hash": "abc123", "ubicacion": "(Madrid)(Espana)", "fecha": "(2024-05)"}
        ]}
    }

    resultado = check_integridad_archivos(data)

    assert resultado["problemas"][0]["tipo"] == "archivo_vacio"

def test_integridad_archivos_hash_vacio(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"hola")

    data = {
        "clasificados": {"items": [
            {"ruta": str(ruta), "hash": "", "ubicacion": "(Madrid)(Espana)", "fecha": "(2024-05)"}
        ]}
    }

    resultado = check_integridad_archivos(data)

    assert resultado["problemas"][0]["tipo"] == "hash_vacio"
    