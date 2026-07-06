# tests/servicios/test_archivo_service.py

import os
from autodiagnostico.servicios.archivo_service import borrar_archivo, mover_archivo, calcular_hash

def test_borrar_archivo(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"hola")

    borrar_archivo(str(ruta))
    assert not ruta.exists()

def test_mover_archivo(tmp_path):
    origen = tmp_path / "origen.jpg"
    destino = tmp_path / "destino.jpg"

    origen.write_bytes(b"hola")

    mover_archivo(str(origen), str(destino))

    assert not origen.exists()
    assert destino.exists()

def test_calcular_hash(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"hola")

    hash_calculado = calcular_hash(str(ruta))
    assert isinstance(hash_calculado, str)
    assert len(hash_calculado) > 0
    