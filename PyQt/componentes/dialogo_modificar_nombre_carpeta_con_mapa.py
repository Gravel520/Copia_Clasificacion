'''
Script en Python.
'''

import json, re, os, shutil
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCompleter, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
from copia_clasificador_fotos import cargar_json_unico, guardar_json_unico
from componentes.geodatos_api import obtener_paises_es, obtener_ciudades
from config_paths import ruta_json_unico
from utils.utils_cache import cargar_cache, guardar_cache, normalizar_texto

# ---------------------------------------------------------
# Puente Python ↔ JavaScript
# ---------------------------------------------------------
class Bridge(QObject):
    coordenadasSeleccionadas = pyqtSignal(float, float, str, str, str)

    @pyqtSlot(float, float, str, str, str)
    def enviarCoordenadas(self, lat, lon, ciudad, pais, clave):
        self.coordenadasSeleccionadas.emit(lat, lon, ciudad, pais, clave)

# ---------------------------------------------------------
# DIÁLOGO COMPLETO
# ---------------------------------------------------------
class DialogoModificarNombreCarpetaMapa(QDialog):
    generarMapaManual = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Modificar Nombre de Carpeta")
        self.resize(900, 500)

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

        # Obtener paises.
        paises = obtener_paises_es()
        completer_paises = QCompleter(paises)
        completer_paises.setCaseSensitivity(Qt.CaseInsensitive)

        # País
        lbl_pais = QLabel("País:")
        lbl_pais.setStyleSheet("font-weight: bold;")
        bloque_ubicacion.addWidget(lbl_pais)
        self.input_pais = QLineEdit()
        self.input_pais.setEnabled(False)
        bloque_ubicacion.addWidget(self.input_pais)

        # Ciudad
        lbl_ciudad = QLabel("Ciudad:")
        lbl_ciudad.setStyleSheet("font-weight: bold;")
        bloque_ubicacion.addWidget(lbl_ciudad)
        self.input_ciudad = QLineEdit()
        #self.input_ciudad.returnPressed.connect(self._geocodificar_y_actualizar_mapa)
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
        self.data = cargar_cache()

        ciudades_js = []
        for clave, coords in self.data.items():
            ciudad, pais = self.separar_ciudad_pais(clave)

            ciudades_js.append({
                "ciudad": ciudad,
                "pais": pais,
                "clave": clave,
                "lat": coords[0],
                "lon": coords[1]
            })
        
        ciudades_json_str = json.dumps(ciudades_js)

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

                var pybridge = null;

                new QWebChannel(qt.webChannelTransport, function(channel) {{
                    pybridge = channel.objects.pybridge;
                }});

                // Lista de ciudades desde Python
                var CIUDADES_JSON = {ciudades_json_str};
                var ciudades = CIUDADES_JSON;

                // Crear marcadores
                ciudades.forEach(function(item) {{
                    var marker = L.marker([item.lat, item.lon]).addTo(map);

                    marker.bindTooltip("Ubicación:" + item.ciudad + ", " + item.pais);

                    marker.on('click', function() {{
                        if (pybridge) {{
                            pybridge.enviarCoordenadas(item.lat, item.lon, item.ciudad, item.pais, item.clave);
                        }}
                    }});
                }});

                var bounds = [];
                ciudades.forEach(function(item) {{
                    bounds.push([item.lat, item.lon]);
                }});

                map.fitBounds(bounds);
                
            </script>
        </body>
        </html>
        """

        self.view.page().setHtml(html, QUrl("qrc:///"))

    def separar_ciudad_pais(self, clave):
        partes = re.findall(r'\((.*?)\)', clave)
        if len(partes) == 2:
            ciudad = partes[0].strip()
            pais = partes[1].strip()
            return ciudad, pais
        return None, None

    # ---------------------------------------------------------
    # Recibir coordenadas desde el mapa
    # ---------------------------------------------------------
    def _recibir_coordenadas(self, lat, lon, ciudad, pais, clave_original):
        self.lat = lat
        self.lon = lon
        self.label_lat.setText(f"Latitud: {lat:.6f}")
        self.label_lon.setText(f"Longitud: {lon:.6f}")

        # Rellenar ciudad y pais
        self.input_ciudad.setText(ciudad)
        self.input_pais.setText(pais)

        self.clave_original = clave_original

    # --------------------------------------------------------------
    # Actualizar el archivo unificado en los campos ruta y ubicación
    # --------------------------------------------------------------
    def _actualizar_archivo_unificado(self, ciudad_nueva, pais_nuevo):
        data = cargar_json_unico(ruta_json_unico())

        items = data["clasificados"]["items"]

        # Clave antigua y nueva
        clave_antigua = self.clave_original
        clave_nueva = f"({ciudad_nueva})({pais_nuevo})"

        for item in items:
            if item["ubicacion"] == clave_antigua:

                # 1. Actualizar ubicacion
                item["ubicacion"] = clave_nueva

                # 2. Actualizar ruta (y renombrar carpeta)
                ruta_antigua = item["ruta"]

                # 3. Extraer carpeta
                carpeta_antigua = os.path.dirname(ruta_antigua)

                # Construir carpeta nueva
                fecha = item["fecha"]
                carpeta_nueva = os.path.join(
                    os.path.dirname(carpeta_antigua),
                    f"({ciudad_nueva})({pais_nuevo}){fecha}"
                )

                # Renombrar carpeta física si existe
                if os.path.exists(carpeta_antigua):
                    shutil.move(carpeta_antigua, carpeta_nueva)

                # Actualizar ruta del archivo
                item["ruta"] = os.path.join(carpeta_nueva, os.path.basename(ruta_antigua))

        guardar_json_unico(ruta_json_unico(), data)

        # Generamos el mapa manualmente.


    # ---------------------------------------------------------
    # Validar y devolver datos
    # ---------------------------------------------------------
    def _validar(self):
        ciudad = normalizar_texto(self.input_ciudad.text().strip())
        pais = normalizar_texto(self.input_pais.text().strip())

        if not ciudad or not pais:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return
        
        if self.lat is None or self.lon is None:
            QMessageBox.warning(self, "Error", "Debes seleccionar una ubicación en el mapa.")
            return

        # Guardar en cache
        cache = cargar_cache()

        # Eliminar la clave original
        if self.clave_original in cache:
            del cache[self.clave_original]

        nueva_clave = f"({ciudad})({pais})"
        cache[nueva_clave] = [self.lat, self.lon]
        guardar_cache(cache)

        # Actualizar archivo unificado
        self._actualizar_archivo_unificado(ciudad, pais)

        QMessageBox.information(self, "Modificar Carpeta", "La carpeta se ha modificado correctamente.")
        self.generarMapaManual.emit()
        self.accept()

    def _separador(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #bbb;")
        return sep
