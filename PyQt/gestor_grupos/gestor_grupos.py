'''

'''

import json
import os, time
import folium
from folium.plugins import MarkerCluster
from PyQt5.QtWidgets import QMessageBox, QApplication
from componentes.controles import SpinnerOverlay
from config_paths import (
    ruta_json_grupos, get_ruta_mapa_grupos_html,
    get_ruta_principal
)

class GestorGrupos():
    def __init__(self):
        self.ruta_grupos = ruta_json_grupos()
        self.data = self._cargar_grupos()
        self.salida = get_ruta_mapa_grupos_html()

    # ---------------------------------------------------------
    # CARGA Y GUARDADO
    # ---------------------------------------------------------
    def _cargar_grupos(self):
        if not os.path.exists(ruta_json_grupos()):
            return {"grupos": []}
        with open(ruta_json_grupos(), "r", encoding="utf-8") as f:
            return json.load(f)
        
    def _guardar(self):
        with open(ruta_json_grupos(), "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    # ---------------------------------------------------------
    # CRUD DE GRUPOS
    # ---------------------------------------------------------
    def crear_grupo(self, nombre, carpetas):
        # Evitar duplicados rápidos en desarrollo
        if any(g["nombre"] == nombre for g in self.data["grupos"]):
            return
        
        self.data["grupos"].append({
            "nombre": nombre,
            "carpetas": carpetas
        })
        self._guardar()

    def modificar_grupo(self, nombre_original, nuevo_nombre=None, nuevas_carpetas=None):
        for grupo in self.data["grupos"]:
            if grupo["nombre"] == nombre_original:
                if nuevo_nombre:
                    grupo["nombre"] = nuevo_nombre
                if nuevas_carpetas is not None:
                    grupo["carpetas"] = nuevas_carpetas
                break
        self._guardar()

    def eliminar_grupo(self, nombre):
        self.data["grupos"] = [g for g in self.data["grupos"] if g["nombre"] != nombre]
        self._guardar()

    def obtener_grupos(self):
        return self.data["grupos"]
    
    def obtener_grupo(self, nombre):
        return next((g for g in self.data["grupos"] if g["nombre"] == nombre), None)
    
    # ---------------------------------------------------------
    # GENERACIÓN DE MAPA GLOBAL DE GRUPOS
    # ---------------------------------------------------------
    def generar_mapa_todos_los_grupos_logica(self, fotos_json, salida=None):
        if salida is None:
            salida = self.salida

        # Crear mapa base centrado de manera general (España)
        m = folium.Map(
            location=[40.41, -3.70],
            zoom_start=5,
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr="OpenStreetMap"            
        )
        cluster = MarkerCluster().add_to(m)
        grupos_con_datos = 0

        # 1. INYECTAR SCRIPT DE QWEBCHANNEL (Igual que en tu otro mapa)
        m.get_root().html.add_child(folium.Element("""
            <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script>
            new QWebChannel(qt.webChannelTransport, function(channel) {
                window.bridge = channel.objects.bridge;
            });

            function enviarRuta(ruta) {
                if (window.bridge && typeof window.bridge.recibirRuta === 'function') {
                    window.bridge.recibirRuta(ruta);
                }
            }

            function enviarListaArchivos(datos) {
                if (window.bridge && typeof window.bridge.recibirListaArchivos === 'function') {
                    window.bridge.recibirListaArchivos(datos);
                }
            }
            </script>
        """))

        coordenadas_totales = []

        # Iterar por cada grupo registrado en la configuración
        for grupo in self.obtener_grupos():
            grupo_nombre = grupo["nombre"]
            carpetas_originales = grupo["carpetas"]
            carpetas_busqueda = [os.path.normpath(carpeta).lower() for carpeta in carpetas_originales]

            # Filtrar fotos pertenecientes a este grupo específico
            fotos_grupo = []
            for foto in fotos_json["clasificados"]["items"]:
                if foto.get("latitud") is None or foto.get("longitud") is None:
                    continue
                ruta_normalizada = os.path.normpath(foto["ruta"]).lower()
                if any(carpeta in ruta_normalizada for carpeta in carpetas_busqueda):
                    fotos_grupo.append(foto)

            # Generar la lista de rutas del grupo.
            lista_rutas = [f["ruta"].replace("\\", "/") for f in fotos_grupo]
            lista_json = json.dumps(lista_rutas)

            if not fotos_grupo:
                QMessageBox.warning(
                    None,
                    "Error Gestor de Grupos",
                    f"Grupo '{grupo_nombre}': Sin fotos válidas con\ncoordenadas."
                )
                continue

            grupos_con_datos += 1

            # Calcular la ubicación media de las fotos para posicionar el mapa
            lats = [float(f["latitud"]) for f in fotos_grupo]
            lons = [float(f["longitud"]) for f in fotos_grupo]
            lat_centro = sum(lats) / len(lats)
            lon_centro = sum(lons) / len(lons)

            coordenadas_totales.append([lat_centro, lon_centro])

            # Constriuimos el diccionario directamente en Python para pasalo limpio
            #   a JavaScript
            diccionario_fotos = {}
            for f in fotos_grupo:
                r_segura = f.get("ruta", "").replace("\\", "/")
                nombre_archivo = os.path.basename(r_segura)
                diccionario_fotos[nombre_archivo] = r_segura

            # 2. GENERAR ENLACES QUE LLAMAN A TU FUNCIÓN enviarRuta()
            enlaces_html = ""
            for carpeta in carpetas_originales:
                # 1. Combinamos la ruta principal con la carpeta del bucle en Python de forma segura.
                ruta_completa_sistema = os.path.join(get_ruta_principal(), carpeta)

                # 2. Reemplazamos TODAS las barras invertidas por barras normales "/"
                #   JavaScript no se romperá y Python (en el QTableWidget) aceptará la ruta específica
                ruta_para_js = ruta_completa_sistema.replace("\\", "/")

                enlaces_html += f"""
                <a href="#" 
                    style="display: block; color: #3498db; margin-top: 5px; text-decoration: none; font-size: 11px; word-break: break-all;"
                    onclick="enviarRuta('{ruta_para_js}'); return false;">
                    📁 {carpeta}
                </a>
                """

            # 3. CONTENIDO VISUAL DEL POPUP (Con lista de enlaces)
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 13px; width: 220px; max-height: 200px; overflow-y: auto;">
                <b style="color: #2c3e50; font-size: 14px;">{grupo_nombre}</b><br>
                <hr style="margin: 4px 0; border: 0; border-top: 1px solid #ccc;">

                <a href="#"
                onclick='enviarListaArchivos({{
                    rutas: {lista_json},
                    titulo: "{grupo_nombre}"
                }}); return false;'
                style="color:#e67e22; font-weight:bold; text-decoration:none;">
                📷 Total archivos: {len(fotos_grupo)}
                </a>

                <div style="margin-top: 8px; font-weight: bold; color: #7f8c8d;">Selecciona una ruta:</div>
                {enlaces_html}
            </div>
            """

            # DISEÑO CSS DEL MARCADOR NARANJA BRILLANTE (Gota Estilizada con Sombra)
            estilo_marcador_naranja = """
            <div style="
                position: relative;
                width: 30px;
                height: 30px;
                background-color: #FF6600;
                border-radius: 50% 50% 50% 0;
                transform: rotate(-45deg);
                box-shadow: 0px 2px 5px rgba(0,0,0,0.5);
                border: 2px solid #FFFFFF;
                left: -15px;
                top: -30px;
            ">
                <!-- Punto blanco central del marcador -->
                <div style="
                    width: 10px;
                    height: 10px;
                    background-color: white;
                    border-radius: 50%;
                    position: absolute;
                    top: 8px;
                    left: 8px;
                "></div>
            </div>
            """

            # CREACIÓN DEL ICONO PERSONALIZADO
            icono_personalizado = folium.DivIcon(
                html=estilo_marcador_naranja,
                icon_size=(30, 30),
                icon_anchor=(0, 0)
            )

            # Crear marcados folium básico
            marker = folium.Marker(
                location=[lat_centro, lon_centro],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=grupo_nombre,
                icon=icono_personalizado
            )
            marker.add_to(cluster)
            
            # INYECCIÓN DIRECTA DE METADATOS DE BÚSQUEDA EN JAVASCRIPT
            # Unimos las carpetas separadas por un espacio para facilitar la búsqueda
            texto_busqueda_carpetas = " ".join(carpetas_originales).replace("\\", "/")
            
            script_metadatos = f"""
            <script>
            setTimeout(function() {{
                var m_objeto = {marker.get_name()};
                if (m_objeto) {{
                    // Forzamos la creación de las propiedades directamente en el objeto de JS
                    m_objeto.meta_grupo_nombre = {json.dumps(grupo_nombre)};
                    m_objeto.meta_carpetas_texto = {json.dumps(texto_busqueda_carpetas)};
                }}
            }}, 200);
            </script>
            """
            m.get_root().html.add_child(folium.Element(script_metadatos))

        # Definimos el panel de búsqueda avanzado actualizado
        m.get_root().html.add_child(folium.Element(f"""
            <style>
            #panelFiltros {{
                position: fixed;
                top: 8px;
                left: 48px;
                z-index: 9999;
                background: rgba(255, 255, 255, 0.85);
                padding: 6px 8px;
                border-radius: 6px;
                box-shadow: 0 0 4px rgba(0,0,0,0.25);
                font-family: sans-serif;
                font-size: 11px;
                line-height: 1.2;
            }}
            #panelFiltros input {{
                width: 120px;
                font-size: 11px;
                padding: 2px 4px;
                margin-top: 2px;
                margin-bottom: 4px;
            }}
            #panelFiltros button {{
                font-size: 11px;
                padding: 3px 6px;
                margin-top: 4px;
            }}
            </style>

            <div id="panelFiltros">
                <label><b>Nombre Grupo</b></label><br>
                <input type="text" id="fGrupo"><br>

                <label><b>(Ciudad/País/Fecha)</b></label><br>
                <input type="text" id="fContenido"><br>

                <button onclick="filtrarGrupos()">Filtrar</button>
                <button onclick="resetearGrupos()">Resetear</button>
            </div>

            <script>
            window.todosLosMarcadoresGrupo = [];

            // Capturamos todos los marcadores del cluster una vez inicializado el mapa
            setTimeout(function() {{
                {cluster.get_name()}.eachLayer(function(layer) {{
                    window.todosLosMarcadoresGrupo.push(layer);
                }});
            }}, 800);

            function filtrarGrupos() {{
                let g = document.getElementById("fGrupo").value.toLowerCase().trim();
                let c = document.getElementById("fContenido").value.toLowerCase().trim();
                
                let visibles = [];
                let total = 0;

                window.todosLosMarcadoresGrupo.forEach(function(layer) {{
                    // Leemos las variables directamente desde el objeto nativo
                    let grupoNombre = layer.meta_grupo_nombre ? layer.meta_grupo_nombre.toLowerCase() : "";
                    let carpetasTexto = layer.meta_carpetas_texto ? layer.meta_carpetas_texto.toLowerCase() : "";

                    // Si no se han escrito filtros, la condición se da por verdadera automáticamente
                    let coincideGrupo = g === "" || grupoNombre.includes(g);
                    let coincideContenido = c === "" || carpetasTexto.includes(c);

                    if (coincideGrupo && coincideContenido) {{
                        if (!{cluster.get_name()}.hasLayer(layer)) {{
                            {cluster.get_name()}.addLayer(layer);
                        }}
                        if (layer.getLatLng) visibles.push(layer.getLatLng());
                        total++;
                    }} else {{
                        {cluster.get_name()}.removeLayer(layer);
                    }}
                }});

                if (total === 0) {{
                    document.getElementById("noResultados").style.display = "block";
                }} else {{
                    document.getElementById("noResultados").style.display = "none";
                }}

                if (visibles.length === 1) {{
                    {m.get_name()}.setView(visibles[0], 10);
                }} else if (visibles.length > 1) {{
                    let bounds = L.latLngBounds(visibles);
                    {m.get_name()}.fitBounds(bounds);
                }}
            }}

            function resetearGrupos() {{
                document.getElementById("fGrupo").value = "";
                document.getElementById("fContenido").value = "";
                document.getElementById("noResultados").style.display = "none";

                let visibles = [];

                window.todosLosMarcadoresGrupo.forEach(function(layer) {{
                    if (!{cluster.get_name()}.hasLayer(layer)) {{
                        {cluster.get_name()}.addLayer(layer);
                    }}
                    if (layer.getLatLng) visibles.push(layer.getLatLng());
                }});

                if (visibles.length === 1) {{
                    {m.get_name()}.setView(visibles[0], 6);
                }} else if (visibles.length > 1) {{
                    let bounds = L.latLngBounds(visibles);
                    {m.get_name()}.fitBounds(bounds, {{ maxZoom: 10 }});
                }}
            }}
            </script>

            <div id="noResultados" 
                style="display:none; position:fixed; top:10px; right:10px; 
                        background:rgba(255,80,80,0.9); color:white; 
                        padding:6px 10px; border-radius:6px; 
                        font-size:12px; z-index:9999;">
                No hay coincidencias
            </div>
        """))

        # Definimos el título flotante y centrado para el mapa
        # Si estás en el otro mapa, solo cambia "MAPA DE GRUPOS" por "MAPA NORMAL"
        texto_titulo = "MAPA DE GRUPOS" 

        m.get_root().html.add_child(folium.Element(f"""
            <style>
            #tituloMapa {{
                position: fixed;
                top: 15px;
                left: 50%;
                transform: translateX(-50%); /* Centrado horizontal perfecto */
                z-index: 9999;
                background: rgba(255, 255, 255, 0.9); /* Fondo blanco semitransparente */
                color: #2c3e50; /* Color de texto elegante */
                padding: 8px 20px;
                border: 2px solid #FF6600; /* Borde naranja a juego con tus marcadores */
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 1px;
                pointer-events: none; /* Permite hacer clic a través del título si hay algo detrás */
            }}
            </style>

            <div id="tituloMapa">
                {texto_titulo}
            </div>
        """))

        if grupos_con_datos > 0:
            if coordenadas_totales:
                m.fit_bounds(coordenadas_totales)
                
            m.save(salida)
            return salida
        
        else:
            return None
        
    def obtener_carpetas(self):        
        try:
            ruta_base = get_ruta_principal()

            carpetas = [
                nombre for nombre in os.listdir(ruta_base)
                if os.path.isdir(os.path.join(ruta_base, nombre))
            ]

            carpetas.sort()
            return carpetas
        except Exception as e:
            QMessageBox.warning(
                None,
                "Error Gestor de Grupos",
                f"Error al obtener las carpetas:\n {e}"
            )
            return []
