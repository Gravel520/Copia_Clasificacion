from autodiagnostico.correcciones.corregir_archivo_huerfano import corregir_archivo_huerfano

def test_corregir_archivo_huerfano():
    data = {
        "clasificados": {"items": []},
        "eliminados": {"items": []}
    }

    problemas = [{
        "ruta": "(Madrid)(Espana)(2024-05)/foto.jpg",
        "tipo": "archivo_huerfano"
    }]

    data = corregir_archivo_huerfano(problemas, data)

    assert len(data["clasificados"]["items"]) == 1
    