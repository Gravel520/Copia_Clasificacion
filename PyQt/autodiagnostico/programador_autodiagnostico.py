'''
Script en Python.
'''

from datetime import datetime, timedelta
from config_manager import load_config, save_config

def toca_ejecutar():
    cfg = load_config()

    if cfg["autodiagnostico_activar"] == "False":
        return False
    
    cantidad = int(cfg["autodiagnostico_cantidad"])
    unidad = cfg["autodiagnostico_unidad"]
    ultima = cfg["autodiagnostico_ultima"]

    if not ultima:
        return True # Primera ejecución
    
    ultima_dt = datetime.strptime(ultima, "%Y-%m-%d")
    ahora = datetime.now()

    if unidad == "dias":
        delta = timedelta(days=cantidad)
    elif unidad == "semanas":
        delta = timedelta(weeks=cantidad)
    elif unidad == "meses":
        delta = timedelta(days=30 * cantidad)

    return ahora - ultima_dt >= delta
