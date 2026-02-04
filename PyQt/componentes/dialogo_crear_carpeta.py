'''

'''

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QMessageBox,
                             QCompleter)
from PyQt5.QtCore import Qt, QTimer
from geopy.geocoders import Nominatim
from componentes.geodatos_api import obtener_paises_es, obtener_ciudades
import datetime

class DialogoCrearCarpeta(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Crear nueva carpeta de destino")
        self.resize(300, 150)

        self.timer = QTimer()
        self.timer.setSingleShot(True)

        layout = QVBoxLayout(self)

        # Obtener paises.
        paises = obtener_paises_es()
        completer_paises = QCompleter(paises)
        completer_paises.setCaseSensitivity(Qt.CaseInsensitive)

        # País.
        layout.addWidget(QLabel("País: "))
        self.input_pais = QLineEdit()
        self.input_pais.setCompleter(completer_paises)        
        self.input_pais.textChanged.connect(self.actualizar_ciudades)
        layout.addWidget(self.input_pais)

        # Ciudad.
        layout.addWidget(QLabel("Ciudad: "))
        self.input_ciudad = QLineEdit()
        layout.addWidget(self.input_ciudad)

        # Fecha (año y mes).
        layout.addWidget(QLabel("Fecha (YYYY-MM): "))
        self.input_fecha = QLineEdit()
        self.input_fecha.setPlaceholderText("2024-07")
        layout.addWidget(self.input_fecha)

        # Botones.
        botones = QHBoxLayout()
        btn_ok = QPushButton("Crear")
        btn_cancel = QPushButton("Cancelar")

        btn_ok.clicked.connect(self._validar)
        btn_cancel.clicked.connect(self.reject)

        botones.addStretch()
        botones.addWidget(btn_ok)
        botones.addWidget(btn_cancel)

        layout.addLayout(botones)

        self.resultado = None

    def actualizar_ciudades(self):
        pais = self.input_pais.text().strip()
        if not pais:
            return
        
        lista_ciudades = obtener_ciudades(pais)
        if not lista_ciudades:
            return
        
        completer_ciudades = QCompleter(lista_ciudades)
        completer_ciudades.setCaseSensitivity(Qt.CaseInsensitive)

        self.input_ciudad.setCompleter(completer_ciudades)

    def _validar(self):
        ciudad = self.input_ciudad.text().strip()
        pais = self.input_pais.text().strip()
        fecha = self.input_fecha.text().strip()

        if not ciudad or not pais or not fecha:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return
        
        # Validar ubicación con Nominatim
        geolocator = Nominatim(user_agent="clasificador_fotos")
        location = geolocator.geocode(f"{ciudad}, {pais}")

        if not location:
            QMessageBox.warning(self, "Error", "No se encontró esa ubicación.")
            return

        # Normalizar nombre de ciudad y pais con Nominatim
        address = location.address.split(', ')
        ciudad = address[-3]
        pais = address[-1]
        
        # Validar fecha.
        try:
            datetime.datetime.strptime(fecha, "%Y-%m")
        except ValueError:
            QMessageBox.warning(self, "Error", "La fecha debe tener formato (YYYY-MM).")
            return
        
        # Todo OK ➡ devolver datos
        self.resultado = (ciudad, pais, fecha)
        self.accept()
