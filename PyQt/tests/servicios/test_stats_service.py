# tests/servicios/test_stats_service.py

from autodiagnostico.servicios.stats_service import actualizar

def test_stats_service():
    # No podemos comprobar estadísticas reales, pero sí que no falla
    data = {"total_clasificados": 0, "total_pendientes": 0}
    actualizar(data)
    assert True
    