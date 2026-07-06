# tests/chequeos/test_json_vs_carpetas.py

import os
from autodiagnostico.chequeos.json_vs_carpetas import check_json_vs_carpetas

def test_json_vs_carpetas_archivo_no_encontrado(tmp_path):
    data = {
        "clasificados": {"items": {
            {"ruta": str(tmp_path / "no_existe.jpg"), "ubicacion": "(Madrid)(Espana)", "fecha": "(2024-05)", "hash": "abc123"}
        }}
    }

    resultado = check_json_vs_carpetas(data, raiz_backup=str(tmp_path))

    assert resultado["problemas"][0]["tipo"] == "archivo_no_encontrado"

def test_json_vs_carpetas_carpeta_incorrecta(tmp_path):
    carpeta_real = tmp_path / "(Madrid)(Espana)(2024-05)"
    carpeta_real.mkdir()

    archivo = carpeta_real / "foto.jpg"
    archivo.write_bytes(b"hola")

    data = {
        "clasificados": {"items": {
            {
                "ruta": str(archivo),
                "ubicacion": "(Madrid)(Espana)",
                "fecha": "(2024-06)", # incorrecto
                 "hash": "abc123"}
        }}
    }

    resultado = check_json_vs_carpetas(data, raiz_backup=str(tmp_path))

    assert resultado["problemas"][0]["tipo"] == "carpeta_incorrecta"
    