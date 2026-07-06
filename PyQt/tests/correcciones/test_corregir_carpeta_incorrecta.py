import os
from autodiagnostico.correcciones.corregir_carpeta_incorrecta import test_corregir_carpeta_incorrecta

def test_corregir_carpeta_incorrecta(tmp_path):
    raiz = tmp_path
    carpeta_real = raiz / "(Madrid)(Espana)(2024-05)"
    carpeta_real.mkdir()

    archivo = carpeta_real / "foto.jpg"
    archivo.write_bytes(b"hola") 

    carpeta_correcta = "(Madrid)(Espana)(2024-06)"

    problemas = [{
        "tipo": "carpeta_incorrecta",
        "ruta": str(archivo),
        "carpeta_esperada": carpeta_correcta
    }]

    data = {"clasificados": {"items": []}}

    data = test_corregir_carpeta_incorrecta(problemas, data, raiz_backup=str(raiz))

    destino = raiz / carpeta_correcta / "foto.jpg"
    assert destino.exists()
    