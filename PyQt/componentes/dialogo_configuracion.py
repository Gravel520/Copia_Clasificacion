'''

'''

from PyQt5.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QDialogButtonBox
    )
from ui_files.configurationWindow import DialogConfiguration
from utils.utils_correo import validar
import config_manager
import string
import ctypes
import re

regex = r"^(?!.*\.\.)(?!.*\.$)[a-zA-Z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = DialogConfiguration()
        self.ui.setupUi(self)

        # Desconectar el cierre automático
        btn_ok = self.ui.btn_ok_cancel.button(QDialogButtonBox.Ok)
        btn_ok.clicked.disconnect()
        btn_ok.clicked.connect(self.on_accept)

        self.load_pantalla()

        self.load_values()

        self.ui.cb_unidad.addItems(self.get_windows_drivers())

        self.conectar_botones()

    def load_values(self):
        cfg = config_manager.load_config()

        self.ui.txt_origen.setText(cfg["origen"])
        self.ui.txt_destino.setText(cfg["destino"])
        self.ui.cb_unidad.setCurrentText(cfg["unidad"])

        # Seleccionar unidad guardada si existe
        idx = self.ui.cb_unidad.findText(cfg["unidad"])
        if idx >= 0:
            self.ui.cb_unidad.setCurrentIndex(idx)

        self.ui.cb_pantalla.setCurrentText(cfg["pantalla"])

        self.ui.txt_correo.setText(cfg["correo"])
        self.ui.txt_password.setText(cfg["password"])

    def save_values(self):       
        data = {
            "origen": self.ui.txt_origen.text(),
            "destino": self.ui.txt_destino.text(),
            "unidad": self.ui.cb_unidad.currentText(),
            "pantalla": self.ui.cb_pantalla.currentIndex(),
            # Estos se mantienen sin cambios aquí.
            "ultimo_intervalo": config_manager.settings.value("Estado/ultimo_intervalo", "0"),
            "mapa_generado": config_manager.settings.value("Estado/mapa_generado", "False"),
            "ultima_origen": self.ui.txt_origen.text(),
            "ultima_destino": self.ui.txt_destino.text(),
            "correo": self.ui.txt_correo.text(),
            "password": self.ui.txt_password.text(),
        }
        config_manager.save_config(data)

    def load_pantalla(self):
        self.ui.cb_pantalla.addItems(["Principal", "Clasificación", "Estadística"])

    def get_windows_drivers(self):
        drivers = []
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()

        for letter in string.ascii_uppercase:
            if bitmask & 1:
                unidad = f"{letter}:\\"
                tipo = ctypes.windll.kernel32.GetDriveTypeW(unidad)

                if tipo == 3: #DRIVE_FIXED ➡ solo discos duros/SSD
                    drivers.append(unidad)
                    
            bitmask >>=1
        return drivers
    
    def select_directory(self, titulo, clave):
        # Obtener la última carpeta usada.
        ultima = config_manager.settings.value(f"General/{clave}", "")

        # Abrir el diálogo en esa carpeta si existe
        carpeta_origen = QFileDialog.getExistingDirectory(
            self, 
            titulo,
            ultima
            )
        
        if carpeta_origen:
            # Guardar la carpeta seleccionada.
            config_manager.settings.setValue(f"General/{clave}", carpeta_origen)
            config_manager.settings.sync()

        return carpeta_origen
    
    def conectar_botones(self):
        botones = [
            (self.ui.btn_examinar_origen, self.ui.txt_origen, "Seleccionar la carpeta de origen.", "ultima_origen"),
            (self.ui.btn_examinar_destino, self.ui.txt_destino, "Seleccionar la carpeta de destino", "ultima_destino"),
        ]

        for boton, campo, titulo, clave in botones:
            boton.clicked.connect(
                lambda _, c=campo, t=titulo, cl=clave: self._seleccionar_y_asignar(c, t, cl)
                )

    def _seleccionar_y_asignar(self, campo, titulo, clave):
        carpeta = self.select_directory(titulo, clave)
        if carpeta: # Solo si el usuario NO canceló
            campo.setText(carpeta)

    def on_accept(self):
        if validar(self.ui.txt_correo):
            self.ui.txt_correo.setStyleSheet("")

            self.save_values()
            self.accept()

        else:
            self.ui.txt_correo.setStyleSheet("border: 2px solid red;")
            self.ui.txt_correo.setFocus()
