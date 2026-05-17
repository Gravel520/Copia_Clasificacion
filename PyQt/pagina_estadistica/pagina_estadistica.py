'''

'''
import os
import json
import re
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
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
from .ventana_carpetas import VentanaCarpetas, VentanaCarpetasVideo

class PaginaEstadisticas(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        # Layout Principal
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(15, 0, 15, 30)

        # ---------------------------------------------------------
        # COLUMNA 1: GRÁFICA
        # ---------------------------------------------------------
        self.col1 = QVBoxLayout()
        self.col1.setSpacing(10)

        self.panel_grafica = self._crear_panel("Gráfica por año")
        self.vista_grafica = QWebEngineView()
        self.vista_grafica.setMinimumHeight(300)
        self.vista_grafica.setMinimumSize(400, 500)
        self.panel_grafica.layout().addWidget(self.vista_grafica)
        self.col1.addWidget(self.panel_grafica)

        # ---------------------------------------------------------
        # COLUMNA 2: MAPA DE CALOR
        # ---------------------------------------------------------
        self.col2 = QVBoxLayout()
        self.col2.setSpacing(10)

        self.panel_mapa = self._crear_panel("Mapa de calor")
        self.vista_mapa = QWebEngineView()
        self.vista_mapa.setMinimumHeight(300)
        self.vista_mapa.setMinimumSize(400, 500)
        self.panel_mapa.layout().addWidget(self.vista_mapa)
        self.col2.addWidget(self.panel_mapa)

        # ---------------------------------------------------------
        # COLUMNA 3: GENERALES + EXIF + CLASIFICADOS
        # ---------------------------------------------------------
        self.col3 = QVBoxLayout()
        self.col3.setSpacing(10)

        self.panel_generales = self._crear_panel("Generales")
        self.panel_generales.setFixedHeight(200)

        self.panel_exif = self._crear_panel("Datos EXIF")
        self.panel_exif.setFixedHeight(200)

        self.panel_clasificacion = self._crear_panel("Clasificación")
        self.panel_clasificacion.setFixedHeight(200)

        self.col3.addWidget(self.panel_generales)
        self.col3.addWidget(self.panel_exif)        
        self.col3.addWidget(self.panel_clasificacion)  
        self.col3.addStretch()      

        # ---------------------------------------------------------
        # Añadir las 3 columnas al layout principal
        # ---------------------------------------------------------
        self.main_layout.addLayout(self.col1, stretch=3)
        self.main_layout.addLayout(self.col2, stretch=3)
        self.main_layout.addLayout(self.col3, stretch=1)

        # Tamaño total de la página
        self.setMinimumSize(1100, 550)

        self.actualizar_datos()

    def showEvent(self, a0):
        super().showEvent(a0)
        self.actualizar_datos()

    def actualizar_datos(self):
        # Refresca todos los componentes con datos nuevos
        # 1. Refrescar paneles de texto (limpiar y llenar)
        self._limpiar_layout(self.panel_generales.layout())
        self._limpiar_layout(self.panel_exif.layout())
        self._limpiar_layout(self.panel_clasificacion.layout())

        self._llenar_panel_generales(self.panel_generales)        
        self._llenar_panel_exif(self.panel_exif)
        self._llenar_panel_clasificacion(self.panel_clasificacion)

        # 2. Refrescar Gáfica
        self.vista_grafica.setHtml(self._obtener_html_grafica(), QUrl("https://cdn.jsdelivr.net"))

        # 3. Refrescar Mapa
        self.vista_mapa.setHtml(self._obtener_html_mapa(), QUrl("https://cdn.jsdelivr.net"))

    def _limpiar_layout(self, layout):
        # Elimina los widget existentes para no duplicarlos al refrescar
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

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
        try:
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

            total_carpetas = len(carpetas)-1 if "(Sin_GPS)(Sin_GPS)(0000-00)" in carpetas else len(carpetas)

            # Mostrar datos
            # 1. Mostrar total del número de fotos.
            panel.layout().addWidget(QLabel(f"      Total fotos: {total_fotos}"))

            # 2. Mostrar total vídeos con botón.
            label_videos = QLabel(f"      Total vídeos: {total_videos}")
            label_videos.setCursor(Qt.CursorShape.PointingHandCursor)
            label_videos.setStyleSheet("QLabel:hover {color: blue; text-decoration: underline;}")
            # Le asignamos la función al hacer clic (usando un evento mousePress)
            label_videos.mousePressEvent = lambda event: self._mostrar_tabla_info("videos")
            panel.layout().addWidget(label_videos)

            # 3. Mostrar tamaño total de los archivos.
            panel.layout().addWidget(QLabel(f"      Tamaño total: {total_tamano/1024/1024:.2f} MB"))

            # 4. Mostrar cantidad de carpetas con botón.            
            label_carpetas = QLabel(f"      Carpetas: {total_carpetas}")
            label_carpetas.setCursor(Qt.CursorShape.PointingHandCursor)
            label_carpetas.setStyleSheet("QLabel:hover {color: blue; text-decoration: underline;}")
            # Le asignamos la función al hacer click (usando un evento mousePress)
            label_carpetas.mousePressEvent = lambda event: self._mostrar_tabla_info("clasificados")
            panel.layout().addWidget(label_carpetas)

        except:
            pass

    def _obtener_html_grafica(self):
        datos = self.fotos_por_anio()

        labels = list(datos.keys())
        valores = list(datos.values())

        return f"""
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
    

    def _obtener_html_mapa(self):
        coords = self.generar_coords_mapa_calor_desde_json()
        coords_js = json.dumps(coords)  # lista Python → array JS

        return f"""
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
            <div id="contadorFotos" 
                style="
                    position:absolute;
                    bottom:20px;
                    left:20px;
                    background:white;
                    color:black;
                    padding:8px 12px;
                    border-radius:6px;
                    font-size:14px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial;
                    z-index:9999;
                ">
                Fotos visibles: 0
            </div>
            <script>
                var map = L.map('map').setView([40.4168, -3.7038], 5);

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 18
                }}).addTo(map);

                // 🔹 aquí definimos coords en JS
                var coords = {coords_js};

                var heat = L.heatLayer(coords, {{
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

                if (coords.length > 0) {{
                    var bounds = new L.LatLngBounds(coords);
                    map.fitBounds(bounds);
                }}

                map.on("moveend", contarFotosEnPantalla);
                map.on("zoomend", contarFotosEnPantalla);

                function contarFotosEnPantalla() {{
                    var bounds = map.getBounds();
                    var contador = 0;

                    coords.forEach(function(p) {{
                        if (bounds.contains(p)) {{
                            contador++;
                        }}
                    }});

                    document.getElementById("contadorFotos").innerText =
                        "Archivos visibles: " + contador;
                }}
            </script>
        </body>
        </html>
        """

    def _llenar_panel_exif(self, panel):
        try:
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
        except:
            pass

    def _llenar_panel_clasificacion(self, panel):
        data = cargar_json_unico(ruta_json_unico())        
        total_clasificados = data["stats"]["total_clasificados"]
        total_pendientes = data["stats"]["total_pendientes"]
        total_eliminados = data["stats"]["total_eliminados"]

        self.agregar_label_con_fondo(f"      Clasificados: {total_clasificados}", "green", panel)
        self.agregar_label_con_fondo(f"      Pendientes: {total_pendientes}", "orange", panel)
        self.agregar_label_con_fondo(f"      Eliminados: {total_eliminados}", "red", panel)

    def agregar_label_con_fondo(self, texto, color, panel):
        label = QLabel(texto)
        label.setStyleSheet(f"""background-color: {color};
                            padding: 5px;""")
        panel.layout().addWidget(label)

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
    
    def _mostrar_tabla_info(self, opcion):
        data = cargar_json_unico(ruta_json_unico())

        ventana = VentanaCarpetas(data) if opcion == "clasificados" else VentanaCarpetasVideo(data)
        ventana.show()
