'''

'''
import os
import json
import re
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
    QSizePolicy, QGroupBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QRect
from componentes.dialogo_crear_carpeta_con_mapa import DialogoCrearCarpetaConMapa
from utils.utils_cache import cargar_cache
from config_paths import (
    get_ruta_principal, extensiones_validas, ruta_json_unico
    )
from copia_clasificador_fotos import cargar_json_unico

class PaginaEstadisticas(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        # Composición de la pantalla en filas y columnas
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 0, 15, 30)

        # ---------------------------------------------------------
        # COLUMNA 1: GRÁFICA
        # ---------------------------------------------------------
        col1 = QVBoxLayout()
        col1.setSpacing(10)

        panel_grafica = self._crear_panel("Gráfica por año")
        grafica = self._crear_grafica_fotos_por_anio()
        grafica.setMinimumSize(400, 500)
        panel_grafica.layout().addWidget(grafica)

        col1.addWidget(panel_grafica)

        # ---------------------------------------------------------
        # COLUMNA 2: MAPA DE CALOR
        # ---------------------------------------------------------
        col2 = QVBoxLayout()
        col2.setSpacing(10)

        panel_mapa = self._crear_panel("Mapa de calor")
        mapa = self._crear_mapa_calor()
        mapa.setMinimumSize(400, 500)
        panel_mapa.layout().addWidget(mapa)

        col2.addWidget(panel_mapa)

        # ---------------------------------------------------------
        # COLUMNA 3: GENERALES + EXIF + CLASIFICADOS
        # ---------------------------------------------------------
        col3 = QVBoxLayout()
        col3.setSpacing(10)

        panel_generales = self._crear_panel("Generales")
        panel_generales.setFixedHeight(200)
        self._llenar_panel_generales(panel_generales)
        col3.addWidget(panel_generales)

        panel_exif = self._crear_panel("Datos EXIF")
        panel_exif.setFixedHeight(200)
        self._llenar_panel_exif(panel_exif)
        col3.addWidget(panel_exif)

        panel_clasificacion = self._crear_panel("Clasificación")
        panel_clasificacion.setFixedHeight(200)
        self._llenar_panel_clasificacion(panel_clasificacion)
        col3.addWidget(panel_clasificacion)

        # ---------------------------------------------------------
        # Añadir las 3 columnas al layout principal
        # ---------------------------------------------------------
        layout.addLayout(col1, stretch=3)
        layout.addLayout(col2, stretch=3)
        layout.addLayout(col3, stretch=1)

        # Tamaño total de la página
        self.setMinimumSize(1100, 550)

    def showEvent(self, a0):
        super().showEvent(a0)
        self.actualizar_datos()

    # ---------------------------------------------------------
    # Crear panel con borde y título
    # ---------------------------------------------------------
    def _crear_panel(self, titulo):
        panel = QGroupBox(titulo)
        panel.setStyleSheet("""
            QGroupBox {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    background: #fafafa;
                    margin-top: 1.5ex; /* Espacio para que el título no pise el borde */
                    font-weight: bold;
            }
            QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left; /* Título arriba a la izquierda */
                    padding: 0 5px;
                    color: #2c3e50;         /* Color azul oscuro grisáceo */
                    font-size: 14px;        /* Tamaño de letra */
                    font-family: 'Segoe UI', Arial; /* Fuente personalizada */
            }
            QFrame {
                border: 1px solid #ccc;
                border-radius: 8px;
                background: #fafafa;
                padding: 6px;
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 20, 10, 10)

        return panel

    # ---------------------------------------------------------
    # DATOS DEL PANEL GENERALES.
    # ---------------------------------------------------------
    def _llenar_panel_generales(self, panel):
        ruta_base = get_ruta_principal()
        carpetas = [d for d in os.listdir(ruta_base) if os.path.isdir(os.path.join(ruta_base, d))]

        total_fotos = 0
        total_videos = 0
        total_tamano = 0

        for carpeta in carpetas:
            ruta = os.path.join(ruta_base, carpeta)
            for archivo in os.listdir(ruta):
                ruta_arch = os.path.join(ruta, archivo)
                if archivo.lower().endswith(extensiones_validas("imagen")):
                    total_fotos += 1
                elif archivo.lower().endswith(extensiones_validas("video")):
                    total_videos += 1

                if os.path.isfile(ruta_arch):
                    total_tamano += os.path.getsize(ruta_arch)

        # Mostrar datos
        panel.layout().addWidget(QLabel(f"      Total fotos: {total_fotos}"))
        panel.layout().addWidget(QLabel(f"      Total vídeos: {total_videos}"))
        panel.layout().addWidget(QLabel(f"      Tamaño total: {total_tamano/1024/1024:.2f} MB"))
        panel.layout().addWidget(QLabel(f"      Carpetas: {len(carpetas)}"))

    def _crear_grafica_fotos_por_anio(self):
        view = QWebEngineView()
        view.setMinimumHeight(300)

        # Datos de ejemplo
        datos = self.fotos_por_anio()

        labels = list(datos.keys())
        valores = list(datos.values())

        html = f"""
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <canvas id="grafica"></canvas>
            <script>
                new Chart(document.getElementById('grafica'), {{
                    type: 'bar',
                    data: {{
                        labels: {labels},
                        datasets: [{{
                            label: 'Fotos por año',
                            data: {valores},
                            backgroundColor: 'rgba(54, 162, 235, 0.5)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{
                                ticks: {{
                                    autoSkip: false,
                                    maxRotation: 0,
                                    minRotation: 0,
                                    font: {{ size: 11}}
                                }}
                            }},
                            y: {{ beginAtZero: true }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        view.setHtml(html, QUrl("https://cdn.jsdelivr.net"))
        return view
    
    def _crear_mapa_calor(self):
        view = QWebEngineView()
        view.setMinimumHeight(300)

        # Ejemplo de coordenadas
        coords = self.generar_coords_mapa_calor_desde_json()

        html = f"""
            <html>
            <head>
                <meta charset="utf-8" />
                <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
                <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
                <style>
                    html, body, #map {{ height: 100%; margin: 0; padding: 0; }}
                </style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    var map = L.map('map').setView([40.4168, -3.7038], 5);

                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        maxZoom: 18
                    }}).addTo(map);

                    var heat = L.heatLayer({coords}, {{
                                radius: 15,
                                blur: 10,
                                maxZoom: 17,
                                minOpacity: 0.4,
                                gradient: {{
                                    0.1: 'blue',
                                    0.4: 'lime',
                                    0.7: 'orange',
                                    1.0: 'red'
                                }}
                            }}).addTo(map);

                            if ({coords}.length > 0) {{
                                var bounds = new L.LatLngBounds({coords});
                                map.fitBounds(bounds);
                            }}
                </script>
            </body>
            </html>
            """

        view.setHtml(html, QUrl("https://cdn.jsdelivr.net"))
        return view
    
    def _llenar_panel_exif(self, panel):
        ruta_base = get_ruta_principal()

        camaras = {}
        isos = {}
        focales = {}

        for carpeta in os.listdir(ruta_base):
            ruta = os.path.join(ruta_base, carpeta)
            for archivo in os.listdir(ruta):
                if archivo.lower().endswith(extensiones_validas("imagen")):
                    ruta_arch = os.path.join(ruta, archivo)
                    try:
                        img = Image.open(ruta_arch)
                        exif = img._getexif()
                        if not exif:
                            continue

                        datos = {TAGS.get(k): v for k, v in exif.items() if k in TAGS}

                        cam = datos.get("Model")
                        iso = datos.get("ISOSpeedRatings")
                        focal = datos.get("FocalLength")

                        if cam:
                            camaras[cam] = camaras.get(cam, 0) + 1
                        if iso:
                            isos[iso] = isos.get(iso, 0) + 1
                        if focal:
                            focales[focal] = focales.get(focal, 0) + 1

                    except:
                        pass
        panel.layout().addWidget(QLabel(f"      Cámara más usada: {max(camaras, key=camaras.get)}"))
        panel.layout().addWidget(QLabel(f"      ISO más frecuente: {max(isos, key=isos.get)}"))
        panel.layout().addWidget(QLabel(f"      Focal más usada: {max(focales, key=focales.get)}"))

    def _llenar_panel_clasificacion(self, panel):
        data = cargar_json_unico(ruta_json_unico())        
        total_clasificados = data["stats"]["total_clasificados"]
        total_pendientes = data["stats"]["total_pendientes"]
        total_eliminados = data["stats"]["total_eliminados"]
        
        panel.layout().addWidget(QLabel(f"      Clasificados: {total_clasificados}"))
        panel.layout().addWidget(QLabel(f"      Pendientes: {total_pendientes}"))
        panel.layout().addWidget(QLabel(f"      Eliminados: {total_eliminados}"))

    def generar_coords_mapa_calor_desde_json(self):
        data = cargar_json_unico(ruta_json_unico())

        coords = []

        for item in data["clasificados"]["items"]:
            lat = item.get("latitud")
            lon = item.get("longitud")

            if lat and lon:
                coords.append([lat, lon])

        return coords
    
    def fotos_por_anio(self):
        data = cargar_json_unico(ruta_json_unico())

        conteo = defaultdict(int)

        for item in data["clasificados"]["items"]:
            fecha = item.get("fecha")
            if not fecha:
                continue

            # Extraer año con regex
            m = re.search(r"\((\d{4})-\d{2}\)", fecha)
            if not m:
                continue

            anio = m.group(1)
            conteo[anio] += 1

        # Devolvemos los datos ordenados por el año, de menor a mayor
        return dict(sorted(conteo.items(), key=lambda x: int(x[0])))
    
    def actualizar_datos(self):
        self._crear_grafica_fotos_por_anio()
        self._crear_mapa_calor()
        self._llenar_panel_generales()
        self._llenar_panel_exif()
        self._llenar_panel_clasificacion()
