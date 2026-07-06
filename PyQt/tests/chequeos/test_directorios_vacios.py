import os
from autodiagnostico.chequeos.directorios_vacios import check_directorios_vacios

def test_directorios_vacios(tmp_path):
    carpeta = tmp_path / "(Madrid)(Espana)(2024-05)"
    carpeta.mkdir()

    resultado = check_directorios_vacios(str(tmp_path))

    assert resultado["problemas"][0]["tipo"] == "directorio_vacio"
    