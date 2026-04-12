'''
Script para validar la dirección de correo electronica
introducida por el usuario.
'''
import re
from PyQt5.QtWidgets import QMessageBox

regex = r"^(?!.*\.\.)(?!.*\.$)[a-zA-Z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

def validar(correo):
    correo = correo.text().strip()

    if re.match(regex, correo):
        return True
    else:
        QMessageBox.critical(
        None, "Correo Electrónico",
        f"Correo electrónico no válido:\n{correo}",
        QMessageBox.Ok)
        return False
    