'''
Usaremos QSettings, que guarda datos en:
    Windows -> Registro
    Linux -> ~/.config
    macOS -> plist
'''

from PyQt5.QtCore import QSettings

class ConfigCorreo:
    def __init__(self):
        self.settings = QSettings("Kataright", "Clasificación Fotos")

    def guardar(self, correo, password):
        self.settings.setValue("correo", correo)
        self.settings.setValue("password", password)

    def cargar(self):
        correo = self.settings.value("correo", "")
        password = self.settings.value("password", "")
        return correo, password
    