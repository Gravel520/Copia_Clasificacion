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
    QDialog, QVBoxLayout, QPushButton, QMessageBox
    )
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSlot, QUrl, QObject, pyqtSignal

class Bridge(QObject):
    coordenadasSeleccionadas = pyqtSignal(float, float)

    @pyqtSlot(float, float)
    def enviarCoordenadas(self, lat, lon):
        self.coordenadasSeleccionadas.emit(lat, lon)

class DialogoMapa(QDialog):
    def __init__(self, lat_inicial= 40.4168, lon_inicial=-3.7038, parent= None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar ubicación en el mapa")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        self.lat = None
        self.lon = None

        self.view = QWebEngineView()
        layout.addWidget(self.view)

        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(self.aceptar)
        layout.addWidget(btn_ok)

        self.bridge = Bridge()
        self.bridge.coordenadasSeleccionadas.connect(self._recibir_coordenadas)

        self.channel = QWebChannel()
        self.channel.registerObject("pybridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        self._cargar_mapa(lat_inicial, lon_inicial)

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

                <!-- WebChannel -->
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

                    function seleccionar(lat, lon) {{
                        if (marker) {{
                            map.removeLayer(marker);
                        }}
                        marker = L.marker([lat, lon]).addTo(map);

                        if (pybridge) {{
                            pybridge.enviarCoordenadas(lat, lon);
                        }}
                    }}

                    map.on('click', function(e) {{
                        seleccionar(e.latlng.lat, e.latlng.lng);
                    }});
                </script>
            </body>
            </html>
            """

        self.view.page().setHtml(html, QUrl("qrc:///"))

    def _recibir_coordenadas(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def aceptar(self):
        if self.lat is None or self.lon is None:
            QMessageBox.warning(self, "Selecciona un punto", "Debes elegir una ubicación en el mapa.")
            return
        self.accept()
