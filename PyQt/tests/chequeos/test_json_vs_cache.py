from autodiagnostico.chequeos.json_vs_cache import check_json_vs_cache

def test_json_vs_cache_hash_vacio():
    data = {
        "clasificados": {"items": [
            {"ruta": "foto.jpg", "hash": "", "ubicacion": "(Madrid)(Espana)", "fecha": "(2024-05)"}
        ]}
    }

    cache = {"(Madrid)(Espana)": [40.416775, -3.703790]}

    resultado = check_json_vs_cache(data, cache)

    assert resultado["problemas"][0]["tipo"] == "hash_vacio"
    