'''

'''

from PyQt5.QtWidgets import QDialog, QFileDialog
from ui_files.configurationWindow import DialogConfiguration
import config_manager
import string
import ctypes

class ConfigDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = DialogConfiguration()
        self.ui.setupUi(self)

        self.load_pantalla()

        self.load_values()

        self.ui.cb_unidad.addItems(self.get_windows_drivers())

        self.conectar_botones()
        self.ui.btn_ok_cancel.accepted.connect(self.save_values)        

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

    def save_values(self):
        data = {
            "origen": self.ui.txt_origen.text(),
            "destino": self.ui.txt_destino.text(),
            "unidad": self.ui.cb_unidad.currentText(),
            "pantalla": self.ui.cb_pantalla.currentText(),
            # Estos se mantienen sin cambios aquí.
            "ultimo_intervalo": config_manager.settings.value("Estado/ultimo_intervalo", "0"),
            "mapa_generado": config_manager.settings.value("Estado/mapa_generado", "False"),
            "ultima_origen": self.ui.txt_origen.text(),
            "ultima_destino": self.ui.txt_destino.text(),            
        }
        config_manager.save_config(data)

    def load_pantalla(self):
        self.ui.cb_pantalla.addItems(["Principal", "Clasificación", "Visor Completo"])

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
            