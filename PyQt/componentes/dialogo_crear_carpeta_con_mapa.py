'''
Script en Python.
Abre un QDialog con un mapa interactivo donde el usuario puede hacer
clic para elegir lat/lon.
La forma más estable, ligera y multiplataforma es usr QWebEngineView
+ Leaflet.js, porque:
    - Leaflet es muy fácil de integrar en un HTML embebido.
    - Puedes carpturar clics en el mapa y devolver lat/lon a Python.
    - No dependes de APIs de pago (como Google Maps).
    - Funciona perfecto dentro de un QDialog.

Que hace este diálogo:
    - Muestra un mapa centrado en una ubicación inicial (opcional).
    - El usuario hace clic en el mapa.
    - Se coloca un marcador.
    - Se envían las coordenadas a Python.
    - El diálogo devuelve (lat, lon) al aceptar.
'''

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCompleter, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl

from componentes.geodatos_api import obtener_paises_es, obtener_ciudades
from config_paths import geocodificador
from utils.utils_cache import cargar_cache, guardar_cache, normalizar_texto
import datetime

# ---------------------------------------------------------
# Puente Python ↔ JavaScript
# ---------------------------------------------------------
class Bridge(QObject):
    coordenadasSeleccionadas = pyqtSignal(float, float)

    @pyqtSlot(float, float)
    def enviarCoordenadas(self, lat, lon):
        self.coordenadasSeleccionadas.emit(lat, lon)

# ---------------------------------------------------------
# DIÁLOGO COMPLETO
# ---------------------------------------------------------
class DialogoCrearCarpetaConMapa(QDialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Crear nueva carpeta de destino")
        self.resize(900, 500)

        self.lat = None
        self.lon = None

        # Layout principal
        layout = QHBoxLayout(self)

        # ---------------------------------------------------------
        # IZQUIERDA -> MAPA
        # ---------------------------------------------------------
        frame_mapa = QFrame()
        frame_mapa.setFrameShape(QFrame.Box)
        frame_mapa.setLineWidth(2)
        frame_mapa.setStyleSheet("""
            QFrame {
                border: 2px solid #888;
                border-radius: 6px;
            }
        """)

        frame_layout = QVBoxLayout(frame_mapa)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        self.view = QWebEngineView()
        frame_layout.addWidget(self.view)

        layout.addWidget(frame_mapa, stretch=2)

        # Bridge y canal
        self.bridge = Bridge()
        self.bridge.coordenadasSeleccionadas.connect(self._recibir_coordenadas)

        self.channel = QWebChannel()
        self.channel.registerObject("pybridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Cargar mapa
        self._cargar_mapa(40.4168, -3.7038)

        # ---------------------------------------------------------
        # DERECHA -> FORMULARIO COMPACTO
        # ---------------------------------------------------------
        form = QVBoxLayout()
        form.setSpacing(15)
        layout.addLayout(form, stretch=1)

        # Bloque ubicación
        bloque_ubicacion = QVBoxLayout()
        bloque_ubicacion.setSpacing(5)
        '''
        # Obtener paises.
        paises = obtener_paises_es()
        completer_paises = QCompleter(paises)
        completer_paises.setCaseSensitivity(Qt.CaseInsensitive)
        '''
        # País
        lbl_pais = QLabel("País:")
        lbl_pais.setStyleSheet("font-weight: bold;")
        bloque_ubicacion.addWidget(lbl_pais)
        self.input_pais = QLineEdit()
        #self.input_pais.setCompleter(completer_paises)
        #self.input_pais.textChanged.connect(self.actualizar_ciudades)
        bloque_ubicacion.addWidget(self.input_pais)

        # Ciudad
        lbl_ciudad = QLabel("Ciudad:")
        lbl_ciudad.setStyleSheet("font-weight: bold;")
        bloque_ubicacion.addWidget(lbl_ciudad)
        self.input_ciudad = QLineEdit()
        self.input_ciudad.returnPressed.connect(self._geocodificar_y_actualizar_mapa)
        bloque_ubicacion.addWidget(self.input_ciudad)

        form.addLayout(bloque_ubicacion)
        form.addWidget(self._separador())

        # Bloque coordenadas
        bloque_coord = QVBoxLayout()
        bloque_coord.setSpacing(5)

        lbl_coord_title = QLabel("Coordenadas:")
        lbl_coord_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        bloque_coord.addWidget(lbl_coord_title)

        # Latitud/longitud
        self.label_lat = QLabel("Latitud: -")
        self.label_lon = QLabel("Longitud: -")
        bloque_coord.addWidget(self.label_lat)
        bloque_coord.addWidget(self.label_lon)

        form.addLayout(bloque_coord)
        form.addWidget(self._separador())

        # Bloque fecha
        bloque_fecha = QVBoxLayout()
        bloque_fecha.setSpacing(5)

        # Fecha
        lbl_fecha = QLabel("Fecha (YYYY-MM):")
        lbl_fecha.setStyleSheet("font-weight: bold; margin-top: 10px;")
        bloque_fecha.addWidget(lbl_fecha)
        self.input_fecha = QLineEdit()
        self.input_fecha.setPlaceholderText("2024-07")
        bloque_fecha.addWidget(self.input_fecha)

        form.addLayout(bloque_fecha)

        # Botones
        btns = QHBoxLayout()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setDefault(False)
        btn_ok.setAutoDefault(False)
        btn_ok.clicked.connect(self._validar)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setDefault(False)
        btn_cancel.setAutoDefault(False)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)

        form.addStretch()
        form.addLayout(btns)

        # Pasar el foco al input del pais
        self.input_pais.setFocus()

    # ---------------------------------------------------------
    # Autocompletar ciudades según el pais
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Cargar mapa con Leaflet
    # ---------------------------------------------------------
    def _cargar_mapa(self, lat, lon):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <style>
                html, body, #map {{ height: 100%; margin: 0; padding: 0; }}
            </style>

            <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        </head>
        <body>
            <div id="map"></div>

            <script>
                var map = L.map('map').setView([{lat}, {lon}], 6);

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19
                }}).addTo(map);

                var marker = null;
                var pybridge = null;

                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    pybridge = channel.objects.pybridge;
                }});

                function centrarYMarcar(lat, lon) {{
                    map.setView([lat, lon], 12);

                    if (marker) {{
                        map.removeLayer(marker);
                    }}
                    marker = L.marker([lat, lon]).addTo(map);

                    if (pybridge) {{
                        pybridge.enviarCoordenadas(lat, lon);
                    }}
                }}

                map.on('click', function(e) {{
                    centrarYMarcar(e.latlng.lat, e.latlng.lng);
                }});
            </script>
        </body>
        </html>
        """

        self.view.page().setHtml(html, QUrl("qrc:///"))

    # ---------------------------------------------------------
    # Recibir coordenadas desde el mapa
    # ---------------------------------------------------------
    def _recibir_coordenadas(self, lat, lon):
        self.lat = lat
        self.lon = lon
        self.label_lat.setText(f"Latitud: {lat:.6f}")
        self.label_lon.setText(f"Longitud: {lon:.6f}")

    # ---------------------------------------------------------
    # Geocodificador país + ciudad y actualizar mapa
    # ---------------------------------------------------------
    def _geocodificar_y_actualizar_mapa(self):
        ciudad = self.input_ciudad.text().strip()
        pais = self.input_pais.text().strip()

        if not ciudad or not pais:
            return
        
        geolocator, reverse = geocodificador()
        location = geolocator(f"{ciudad}, {pais}", language="es")

        if not location:
            QMessageBox.warning(self, "Error", "No se encontró esa ubicación.")
            return
        
        lat = location.latitude
        lon = location.longitude

        self._recibir_coordenadas(lat, lon)

        # Enviar coordenadas al mapa
        js = f"centrarYMarcar({lat}, {lon});"
        self.view.page().runJavaScript(js)

    # ---------------------------------------------------------
    # Validar y devolver datos
    # ---------------------------------------------------------
    def _validar(self):
        ciudad = normalizar_texto(self.input_ciudad.text().strip())
        pais = normalizar_texto(self.input_pais.text().strip())
        fecha = self.input_fecha.text().strip()

        if not ciudad or not pais or not fecha:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return
        
        if self.lat is None or self.lon is None:
            QMessageBox.warning(self, "Error", "Debes seleccionar una ubicación en el mapa.")
            return
        
        # Validar fecha
        try:
            datetime.datetime.strptime(fecha, "%Y-%m")
        except ValueError:
            QMessageBox.warning(self, "Error", "La fecha debe tener formato YYYY-MM.")
            return
        
        # Guardar en cache
        cache = cargar_cache()
        nombre = f"({ciudad})({pais})"
        cache[nombre] = [self.lat, self.lon]
        guardar_cache(cache)

        self.resultado = (ciudad, pais, fecha)
        self.accept()

    def _separador(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #bbb;")
        return sep
