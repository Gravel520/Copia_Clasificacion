# tests/servicios/test_ubicacion_service.py

from autodiagnostico.servicios.ubicacion_service import construir_carpeta

def test_construir_carpeta():
    carpeta = construir_carpeta("(Madrid)(Espana)", "(2024-05)")
    assert carpeta == "(Madrid)(Espana)(2024-05)"
    