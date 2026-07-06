# tests/utils/test_hashing.py

from autodiagnostico.utils.hashing import hash_archivo

def test_hash_archivo(tmp_path):
    ruta = tmp_path / "foto.jpg"
    ruta.write_bytes(b"hola")

    hash_calculado = hash_archivo(str(ruta))
    assert isinstance(hash_calculado, str)
    assert len(hash_calculado) > 0
    