# tests/utils/test_fechas.py

from autodiagnostico.utils.fechas import obtener_fecha

def test_obtener_fecha(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"hola")

    fecha_completa, timestamp, hora = obtener_fecha(str(ruta))

    assert fecha_completa is not None
    assert timestamp is not None
    assert hora is not None
    