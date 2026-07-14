'''

'''

from PyQt5.QtCore import QSettings

settings = QSettings("config.ini", QSettings.IniFormat)

def load_config():
    return {
        "origen": settings.value("Paths/origen", "", str),
        "destino": settings.value("Paths/destino", "", str),
        "unidad": settings.value("General/unidad", "", str),
        "pantalla": settings.value("General/pantalla", "0", str),
        "ultimo_intervalo": settings.value("Estado/ultimo_intervalo", "0", str),
        "mapa_generado": settings.value("Estado/mapa_generado", "False", str),
        "ultima_origen": settings.value("General/ultima_origen", "", str),
        "ultima_destino": settings.value("General/ultima_destino", "", str),
        "correo": settings.value("Compartir/correo", "", str),
        "password": settings.value("Compartir/password", "", str),
        "autodiagnostico_activar": settings.value("Autodiagnostico/activar", "False", str),
        "autodiagnostico_cantidad": settings.value("Autodiagnostico/cantidad", "0", str),
        "autodiagnostico_unidad": settings.value("Autodiagnostico/unidad", "0", str),
        "autodiagnostico_ultima": settings.value("Autodiagnostico/ultima", "0", str),
    }

def save_config(data: dict):
    settings.setValue("Paths/origen", data["origen"])
    settings.setValue("Paths/destino", data["destino"])
    settings.setValue("General/unidad", data["unidad"])
    settings.setValue("General/pantalla", data["pantalla"])
    settings.setValue("Estado/ultimo_intervalo", data["ultimo_intervalo"])
    settings.setValue("Estado/mapa_generado", data["mapa_generado"])
    settings.setValue("General/ultima_origen", data["ultima_origen"])
    settings.setValue("General/ultima_destino", data["ultima_destino"])
    settings.setValue("Compartir/correo", data["correo"])
    settings.setValue("Compartir/password", data["password"])
    settings.setValue("Autodiagnostico/activar", data["autodiagnostico_activar"])
    settings.setValue("Autodiagnostico/cantidad", data["autodiagnostico_cantidad"])
    settings.setValue("Autodiagnostico/unidad", data["autodiagnostico_unidad"])
    settings.setValue("Autodiagnostico/ultima", data["autodiagnostico_ultima"])
    
    settings.sync()
    