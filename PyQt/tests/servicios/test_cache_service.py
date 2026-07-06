# test/servicios/test_cache_service.py

from autodiagnostico.servicios.cache_service import cargar, guardar

def test_cache_service(tmp_path, monkeypatch):
    # Simular archivo de cache
    ruta = tmp_path / "cache.json"
    ruta.write_text('{"(Madrid)(Espana)": [40.416775, -3.703790]}')

    # Monkeypathc para redirigir funciones
    monkeypatch.setattr("copia_clasificador_fotos.CACHE_PATH", str(ruta))

    cache = cargar()
    assert cache["(Madrid)(Espana)"] == [40.416775, -3.703790]

    cache["(Madrid)(Espana)"] = [1, 2]
    guardar(cache)

    nuevo = cargar()
    assert nuevo["(Madrid)(Espana)"] == [1, 2]
    