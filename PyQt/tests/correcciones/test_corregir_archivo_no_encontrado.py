from autodiagnostico.correcciones.corregir_archivo_no_encontrado import corregir_archivo_no_encontrado

def test_corregir_archivo_no_encontrado():
    data = {
        "clasificados": {"items": [
            {"ruta": "no_existe.jpg", "hash": "abc123"}
        ]}
    }

    problemas = [{"ruta": "no_existe.jpg", "tipo": "archivo_no_encontrado"}]

    data = corregir_archivo_no_encontrado(problemas, data)

    assert len(data["clasificados"]["items"]) == 0
    