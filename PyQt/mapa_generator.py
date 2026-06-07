'''
Script en Python.
Con este script vamos a crear un mapa con todos los subdirectorios que
tiene el directorio principal que contiene las fotos 'BackupFotos'.
Cada directorio tiene el nombre '(ciudad)(pais)(año-mes)', así que cada
marca será el nombre de la ciudad y el número de fotos que tiene ese
directorio.

Para crear las marcas en el mapa con la localización del lugar que sea
el nombre del pueblo o ciudad y el pais, la hacemos con la librería
'geopy'. Esta librería convierte nombres de lugares en coordenadas, 
aptas para la geolocalización con 'Folium'.

Así que dividimos el nombre del directorio en ciudad, pais y fecha, 
dividiendo el nombre en 3 partes separadas por '), y posteriormente
le quitaremos a cada parte el primer carácter que será '(', para
quedarnos con el string que nos interesa (ciudad, pais y fecha).

Posteriormente utilizaremos la ciudad y el pais para obtener la 
geolocalización y poder colocar la marca, que contendrá el nombre de
la ciudad y el número de fotos que tiene ese lugar.

Al presionar sobre la marca, se abrirá un cuadro de diálogo con el 
listado de las fotos que hay dentro.
'''

import folium
import os
import time
import datetime
from collections import defaultdict
from copia_clasificador_fotos import cargar_json_unico
from config_paths import (
    get_ruta_mapa_html, get_ruta_principal, ruta_json_unico
    )
from utils.utils_cache import (
    cargar_cache, normalizar_texto
)

# Función para extraer el nombre de la ciudad.
def extraer_ciudad(nombre):
    partes = nombre.split(')')
    if len(partes) < 3:
        print(f'Formato inválido en: {nombre}')
        return 'Desconocido', 'Desconocido', 'Desconocido'
    ciudad = partes[0][1:].strip()
    pais = partes[1][1:].strip()
    fecha = partes[2][1:].strip()
    return ciudad, pais, fecha

def parse_fecha_key(fecha):
    '''
    Intenta convertir 'fecha' en datetime para ordenar cronológicamente.
    Soporta formatos comunes: 'YYYY-MM', 'YYYY-M', 'YYYY-MM-DD', 'YYYY'.
    Si no puede parsear, devuelve la cadena tal cual (orden lexicográfico)
    '''
    formatos = ['%Y-%m', '%Y-%m-%d', '%Y-%m-%d', '%Y-%m', '%Y']
    # Normalizar guiones y ceros (por ejemplo '2021-7' -> '2021-07' si es posible)
    f = fecha.strip()
    # Intentos con formatos comunes
    for fmt in formatos:
        try:
            return datetime.datetime.strftime(f, fmt)
        except Exception:
            # Intentar rellenar mes con cero si vivne 'YYYY-M'
            parts = f.split('-')
            if len(parts) == 2 and len(parts[1]) == 1:
                try:
                    return datetime.datetime.strftime(f.replace('-', '-0', 1), '%Y-%m')
                except Exception:
                    pass
            continue
    # Fallback: devolver la cadena para orden lexicográfica
    return f

def obtener_coordenadas(ciudad, pais):
    nombre = f"({ciudad})({pais})"
    cache = cargar_cache()

    # 1. Si está en cache > usarlo SIEMPRE
    if nombre in cache:
        lat, lon = cache[nombre]
        return lat, lon
    
    # 2. Si no esta > no inventamos nada
    print(f"[WARN] No hay coordenadas en cache para: {nombre}")
    return None

'''
Cuando se reneriza en el navegador, las doblas barras invertidas (\\) se
interpretan como una sola (\), y luego en el navegador escapa esa barra
invertida como parte de una cadena JavaScript, lo que puede terminar 
eliminándola o malinterpretándola.
Para que la ruta se transmita correctamente a PyQt, hay escapar doblemente
las barras invertidas en el HTML embebido dentro del script Python. Es decir,
en el string Python, cada (\) debe ser escrita como (\\\\) para que llegue
como (\\) al HTML, y luego como (\) al JavaScript.
'''
def crear_popup_html(ciudad, pais, entradas):
    html = f"<div style='width:250px;'>"
    for fecha, ruta, num in entradas:
        # Creamos la corrección de las barras barras invertidas para que la
        #   ruta del directorio se interprete correctamente.
        ruta = ruta.replace('\\', '\\\\')
        html += f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
            <span><b>{ciudad}, {pais} - {fecha} ({num} archivos)</b></span>
            <button onclick="enviarRuta('{ruta}')" 
                    style="border:none; background:none; cursor:pointer; padding:0;">
                <svg width="20" height="20" viewBox="0 0 24 24">
                    <path fill="black" d="M12 5c-7.633 0-11 7-11 7s3.367 7 11 7 11-7 11-7-3.367-7-11-7zm0 
                    12c-2.761 0-5-2.239-5-5s2.239-5 
                    5-5 5 2.239 5 5-2.239 5-5 5zm0-8c-1.654 
                    0-3 1.346-3 3s1.346 3 3 3 
                    3-1.346 3-3-1.346-3-3-3z"/>
                </svg>
            </button>
        </div>
        """
    html += "</div>"
    return html    

def generar_mapa(features):
    cache_json_geocoding = cargar_cache()
    coords = list(cache_json_geocoding.values())

    if coords:
        # Calculamos el promedio de latitud y longitud
        lat_centro = sum(p[0] for p in coords) / len(coords)
        lon_centro = sum(p[1] for p in coords) / len(coords)
        coordenadas = [lat_centro, lon_centro]
    else: # Fallback a Madrid si el json está vacío
        lat_centro = 40.4167
        lon_centro = -3.7033

    # Inicializamos la localización en el centro de la localización
    #   del archivo .json
    lat, lon = lat_centro, lon_centro
    mapa = folium.Map(
        location=[lat, lon],
        zoom_start=5
        )
    
    # Formatear tooltip.
    for f in features:
        nombre = f["properties"]["nombre"]

        partes = nombre.split()
        ciudad = " ".join(partes[:-1])
        pais = partes[-1]
        f["properties"]["tooltip"] = f"Ubicación: {ciudad}, {pais}"
    
    # Crear capa GeoJSON
    geojson_layer = folium.GeoJson(
        {"type": "FeatureCollection", "features": features},
        name="Fotos",
        popup=folium.GeoJsonPopup(fields=["popup"], labels=False),
        tooltip=folium.GeoJsonTooltip(fields=["tooltip"], aliases=[""], labels=False)
    ).add_to(mapa)

    mapa_name = mapa.get_name()
    geojson_name = geojson_layer.get_name()

    # Agregar canal de comunicación con PyQt
    mapa.get_root().html.add_child(folium.Element("""
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <script>
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.bridge = channel.objects.bridge;
        });
        function enviarRuta(ruta) {
            window.bridge.recibirRuta(ruta);
        }
        </script>
    """))

    # Definimos el panel de busqueda.
    mapa.get_root().html.add_child(folium.Element(f"""
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
        }}
        #panelFiltros button {{
            font-size: 11px;
            padding: 3px 6px;
            margin-top: 4px;
        }}
        </style>

        <div id="panelFiltros">
            <label><b>Ciudad</b></label><br>
            <input type="text" id="fCiudad"><br>

            <label><b>País</b></label><br>
            <input type="text" id="fPais"><br>

            <label><b>Fecha</b></label><br>
            <input type="text" id="fFecha"><br>

            <button onclick="filtrar()">Filtrar</button>
            <button onclick="resetear()">Resetear</button>
        </div>

        <script>
        function filtrar() {{
            let c = document.getElementById("fCiudad").value.toLowerCase();
            let p = document.getElementById("fPais").value.toLowerCase();
            let f = document.getElementById("fFecha").value.toLowerCase();

            let visibles = [];
            let total = 0;

            {geojson_name}.eachLayer(function(layer) {{
                if (!layer.feature || !layer.feature.properties) return;

                let props = layer.feature.properties;

                let coincide =
                    props.ciudad.toLowerCase().includes(c) &&
                    props.pais.toLowerCase().includes(p) &&
                    props.fecha.toLowerCase().includes(f);

                if (coincide) {{
                    if (!{mapa_name}.hasLayer(layer)) {mapa_name}.addLayer(layer);
                    if (layer.getLatLng) visibles.push(layer.getLatLng());
                    total++;
                }} else {{
                    if ({mapa_name}.hasLayer(layer)) {mapa_name}.removeLayer(layer);
                }}
            }});

            if (total === 0) {{
                document.getElementById("noResultados").style.display = "block";
            }} else {{
                document.getElementById("noResultados").style.display = "none";
            }}

            if (visibles.length === 1) {{
                {mapa_name}.setView(visibles[0], 10);
            }} else if (visibles.length > 1) {{
                let bounds = L.latLngBounds(visibles);
                {mapa_name}.fitBounds(bounds);
            }}
        }}

        function resetear() {{
            document.getElementById("fCiudad").value = "";
            document.getElementById("fPais").value = "";
            document.getElementById("fFecha").value = "";

            document.getElementById("noResultados").style.display = "none";

            let visibles = [];

            {geojson_name}.eachLayer(function(layer) {{
                if (!layer.feature || !layer.feature.properties) return;
                if (!{mapa_name}.hasLayer(layer)) {mapa_name}.addLayer(layer);
                if (layer.getLatLng) visibles.push(layer.getLatLng());
            }});

            if (visibles.length === 1) {{
                {mapa_name}.setView(visibles[0], 8);
            }} else if (visibles.length > 1) {{
                let bounds = L.latLngBounds(visibles);
                {mapa_name}.fitBounds(bounds, {{ maxZoom: 10 }});
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
    texto_titulo = "MAPA DE FOTOS" 

    mapa.get_root().html.add_child(folium.Element(f"""
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
            border: 2px solid #2A81CB; /* Borde naranja a juego con tus marcadores */
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


    if coordenadas:
        mapa.fit_bounds(coordenadas)

    mapa.save(f'{get_ruta_mapa_html()}')

def cargar_datos_desde_historial():
    '''
    Cargamos los datos del archivo unificado. Posteriormente
        obtenemos los datos de los archivos que ya han sido
        clasificados, que serán los que fijemos en el mapa.
    '''
    data = cargar_json_unico(ruta_json_unico())

    historial = data["clasificados"]["items"]

    agrupadas = defaultdict(list)
    combinaciones_unicas = set()

    for item in historial:
        clave = item['ubicacion'] + item['fecha']
        combinaciones_unicas.add(clave)

    for directorio in combinaciones_unicas:
        ruta_directorio = os.path.join(get_ruta_principal(), directorio)
        archivos = os.listdir(ruta_directorio)
        ciudad, pais, fecha = extraer_ciudad(directorio)
        ciudad = normalizar_texto(ciudad)
        pais = normalizar_texto(pais)
        agrupadas[(ciudad, pais)].append((fecha, ruta_directorio, len(archivos)))

    features = []
    for (ciudad, pais), entradas in agrupadas.items():
        coordenadas = obtener_coordenadas(ciudad, pais)
        if not coordenadas:
            continue

        lat, lon = coordenadas

        # Ordenar las entradas por fecha cronológica usando parse_fecha_key
        try:
            entradas_ordenadas = sorted(entradas, key=lambda e: parse_fecha_key(e[0]))
        except Exception:
            entradas_ordenadas = entradas # Fallback si alto falla

        # Crear el HTML del popup con las entradas ordenadas
        html = crear_popup_html(ciudad, pais, entradas_ordenadas)
        feature = {
            "type": "Feature",
            "properties": {
                "nombre": f"{ciudad} {pais}",
                "ciudad": ciudad,
                "pais": pais,
                # Usar las fechas en el mismo orden que en el popup.
                "fecha": ", ".join([e[0] for e in entradas_ordenadas]),
                "popup": html
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        
        features.append(feature)
        time.sleep(1) # Evitar sobrecarga del geocodificador

    # Filtrar features sin propiedades válidas
    features = [
        f for f in features
        if "properties" in f and "nombre" in f["properties"] and "popup" in f["properties"]
    ]
    if features:
        generar_mapa(features)
