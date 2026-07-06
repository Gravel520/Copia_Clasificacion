# tests/utils/test_rutas.py

import os
from autodiagnostico.utils.rutas import carpeta_de_ruta

def test_carpeta_de_ruta(tmp_path):
    carpeta = tmp_path / "carpeta"
    carpeta.mkdir()

    archivo = carpeta / "foto.jpg"
    archivo.write_bytes(b"hola")

    resultado = carpeta_de_ruta(str(archivo))

    assert resultado == "carpeta"
    