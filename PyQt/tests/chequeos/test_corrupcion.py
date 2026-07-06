import os
from autodiagnostico.chequeos.corrupcion import check_archivos_corruptos

def test_imagen_corrupta(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"no_es_una_imagen")

    data = {
        "clasificados": {"items": [
            {"ruta": str(ruta), "ubicacion": "(Madrid)(Espana)", "fecha": "(2024-05)"}
        ]}
    }

    resultado = check_archivos_corruptos(data)

    assert resultado["problemas"][0]["tipo"] == "imagen_corrupta"
    