'''

'''

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QMessageBox,
                             QCompleter)
from PyQt5.QtCore import Qt, QTimer
from geopy.geocoders import Nominatim
from config_paths import geocodificador
from componentes.geodatos_api import obtener_paises_es, obtener_ciudades
from utils.utils_cache import (
    cargar_cache, guardar_cache, normalizar_texto
)
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
        # Obtenemos y normalizamos los datos.
        ciudad = normalizar_texto(self.input_ciudad.text().strip())
        pais = normalizar_texto(self.input_pais.text().strip())
        fecha = self.input_fecha.text().strip()

        if not ciudad or not pais or not fecha:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return
        
        cache = cargar_cache()        
        # Validar ubicación con Nominatim
        geolocator, reverse = geocodificador()
        location = geolocator(
            ciudad,
            country_codes="es, fr, pt",
            language="es"
        )

        if not location:
            QMessageBox.warning(self, "Error", "No se encontró esa ubicación.")
            return

        # Normalizar nombre de ciudad y pais con Nominatim
        address = location.address.split(', ')
        ciudad_norm = normalizar_texto(address[0])
        pais_norm = normalizar_texto(address[-1])

        nombre = f"({ciudad_norm})({pais_norm})"

        if nombre not in cache:
            lat = location.latitude
            lon = location.longitude
            # Guardamos el nuevo registro en el cache de geocoding
            cache[nombre] = [lat, lon]
            guardar_cache(cache)
        
        # Validar fecha.
        try:
            datetime.datetime.strptime(fecha, "%Y-%m")
        except ValueError:
            QMessageBox.warning(self, "Error", "La fecha debe tener formato (YYYY-MM).")
            return
        
        # Todo OK ➡ devolver datos
        self.resultado = (ciudad_norm, pais_norm, fecha)
        self.accept()
