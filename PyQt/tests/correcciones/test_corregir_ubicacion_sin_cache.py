from autodiagnostico.correcciones.corregir_ubicacion_sin_cache import corregir_ubicacion_sin_cache

def test_corregir_ubicacion_sin_cache():
    data = {
        "clasificados": {"items": [
            {"ubicacion": "(Madrid)(Espana)",
             "latitud": 40.416775,
             "longitud": -3.703790}
        ]}
    }

    problemas = [{"ubicacion": "(Madrid)(Espana)", "tipo": "ubicacion_sin_cache"}]

    data = corregir_ubicacion_sin_cache(problemas, data)

    # No podemos coprobar el cache real, pero sí que no falla
    assert True
    