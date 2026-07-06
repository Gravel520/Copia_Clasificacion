# tests/servicios/test_json_service.py

from autodiagnostico.servicios.json_service import cargar_json, guardar_json
import json

def test_json_service(tmp_path):
    ruta = tmp_path / "data.json"

    original = {"hola": "mundo"}
    guardar_json(str(ruta), original)

    cargado = cargar_json(str(ruta))

    assert cargado == original
    