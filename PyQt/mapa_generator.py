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
import json
from collections import defaultdict
from copia_clasificador_fotos import cargar_json_unico
from config_paths import (
    get_ruta_mapa_fotos_html, get_ruta_principal, ruta_json_unico,
    get_ruta_mapa_provincias_html
    )
from utils.utils_cache import (
    cargar_cache, normalizar_texto
)
from folium import IFrame

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
    f = fecha.strip()    
    formatos = ['%Y-%m-%d', '%Y-%m', '%Y']
    # Normalizar guiones y ceros (por ejemplo '2021-7' -> '2021-07' si es posible)
    parts = f.split('-')
    if len(parts) >= 2 and len(parts[1]) == 1:
        parts[1] = parts[1].zfill(2)
        f_normalizada = '-'.join(parts)
    else:
        f_normalizada = f

    for fmt in formatos:
        try:
            dt = datetime.datetime.strptime(f_normalizada, fmt)
            return dt
        except Exception:
            continue

    # Fallback: devolver la cadena para orden lexicográfica
    return f

def obtener_coordenadas(ciudad, pais):
    nombre = f"({ciudad})({pais})"
    cache = cargar_cache() or {}

    if nombre not in cache:
        print(f"[WARN] No hay coordenadas en cache para: {nombre}")
        return None

    val = cache[nombre]

    # Formato nuevo: {"lat": 40.1, "lon": -3.1}
    if isinstance(val, dict):
        if "lat" in val and "lon" in val:
            try:
                lat = float(val["lat"])
                lon = float(val["lon"])
                return lat, lon
            except Exception:
                print(f"[WARN] Coordenadas inválidas en cache para: {nombre}")
                return None
        else:
            print(f"[WARN] Formato de cache inesperado para {nombre}: {val}")
            return None

    # Formato antiguo: [40.1, -3.1]
    if isinstance(val, (list, tuple)) and len(val) >= 2:
        try:
            lat = float(val[0])
            lon = float(val[1])
            return lat, lon
        except Exception:
            # 2. Si no esta > no inventamos nada
            print(f"[WARN] Coordenadas inválidas en cache para: {nombre}")
            return None

    # Formato desconocido
    print(f"[WARN] Formato de cache inesperado para {nombre}: {val}")
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
        ruta_str = str(ruta)
        # Creamos la corrección de las barras barras invertidas para que la
        #   ruta del directorio se interprete correctamente.
        ruta_js = ruta_str.replace('\\', '\\\\')
        html += f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
            <span><b>{ciudad}, {pais} - {fecha} ({num} archivos)</b></span>
            <button onclick="enviarRuta('{ruta_js}')" 
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
    cache_json_geocoding = cargar_cache() or {}
    coords = [v for v in cache_json_geocoding.values() if isinstance(v, (list, tuple)) and len(v) >= 2]

    if coords:
        # Calculamos el promedio de latitud y longitud
        lat_centro = sum(float(p[0]) for p in coords) / len(coords)
        lon_centro = sum(float(p[1]) for p in coords) / len(coords)
        centro = [lat_centro, lon_centro]
    else: # Fallback a Madrid si el json está vacío
        centro = [40.4167, -3.7033]

    # Inicializamos la localización en el centro de la localización
    #   del archivo .json
    mapa = folium.Map(
        location=centro,
        zoom_start=5
        )
    
    # Formatear tooltip.
    for f in features:
        props = f.get("properties", {})
        nombre = props.get("nombre", "")

        partes = nombre.split()
        if len(partes) >= 2:
            ciudad = " ".join(partes[:-1])
            pais = partes[-1]
        else:
            ciudad = props.get("ciudad", "Desconocido")
            pais = props.get("pais", "Desconocido")
        props["tooltip"] = f"Ubicación: {ciudad}, {pais}"
    
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
            border: 2px solid #2A81CB; /* Borde azul a juego con tus marcadores */
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

    # Ajustar vista inicial a todos los puntos si hay features
    puntos = []
    for f in features:
        geom = f.get('geometry', {})
        coords = geom.get('coordinates', [])
        if coords and len(coords) >= 2:
            puntos.append([coords[1], coords[0]])

    if puntos:
        mapa.fit_bounds(puntos)

    # Guardar el mapa
    ruta_salida = get_ruta_mapa_fotos_html()
    try:
        mapa.save(ruta_salida)
    except Exception as e:
        print(f"Error al guardar el mapa: {e}")

def cargar_datos_desde_historial():
    '''
    Cargamos los datos del archivo unificado. Posteriormente
        obtenemos los datos de los archivos que ya han sido
        clasificados, que serán los que fijemos en el mapa.
    '''
    data = cargar_json_unico(ruta_json_unico())
    historial = data.get("clasificados", {}).get("items", [])

    agrupadas = defaultdict(list)
    combinaciones_unicas = set()

    for item in historial:
        ubic = item.get('ubicacion', '')
        fecha = item.get('fecha', '')
        clave = f"{ubic}{fecha}"
        combinaciones_unicas.add(clave)

    for directorio in combinaciones_unicas:
        ruta_directorio = os.path.join(get_ruta_principal(), directorio)
        try:
            archivos = os.listdir(ruta_directorio)
        except Exception:
            print(f"[WARN] No se puede listar {ruta_directorio}, se omite.")
            continue

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
        time.sleep(0.01) # Evitar sobrecarga del geocodificador

    # Filtrar features sin propiedades válidas
    features = [
        f for f in features
        if "properties" in f and "nombre" in f["properties"] and "popup" in f["properties"]
    ]
    if features:
        generar_mapa(features)
    else:
        print("[INFO] No hay features para generar el mapa.")

def agrupar_ciudades_por_provincia():
    """
    Agrupa todas las ciudades por provincia usando:
    - historial de clasificados
    - cache geocoding extendido (lat, lon, provincia, postal
        ciudad, pais)
    """

    # 1. Cargar datos
    data = cargar_json_unico(ruta_json_unico())
    historial = data.get("clasificados", {}).get("items", [])

    cache = cargar_cache() or {}

    # Estructura final:
    # provincia -> lista de ciudades -> lista de entradas (fecha, ruta,
    #   num_archivos)
    provincias = defaultdict(lambda: defaultdict(list))

    # 2. Obtener combinaciones únicas de directorios
    combinaciones_unicas = set()
    for item in historial:
        ubic = item.get("ubicacion", "")
        fecha = item.get("fecha", "")
        clave = f"{ubic}{fecha}"
        combinaciones_unicas.add(clave)

    # 3. Procesar cada directorio
    for directorio in combinaciones_unicas:
        ruta_directorio = os.path.join(get_ruta_principal(), directorio)

        try:
            archivos = os.listdir(ruta_directorio)
        except Exception:
            print(f"[WARN] No se puede listar {ruta_directorio}, se omite.")
            continue

        ciudad, pais, fecha = extraer_ciudad(directorio)
        ciudad = normalizar_texto(ciudad)
        pais = normalizar_texto(pais)

        # 4. Buscar provincia en cache
        clave_cache = f"({ciudad})({pais})"
        info = cache.get(clave_cache)

        if not info:
            print(f"[WARN] No hay información de geocoding para: {clave_cache}, se omite.")
            continue

        provincia = info.get("provincia", "")
        lat = info.get("lat")
        lon = info.get("lon")

        if not provincia:
            print(f"[WARN] No hay provincia en geocoding para: {clave_cache}, se omite.")
            continue

        # 5. Añadir entrada a la provincia correspondiente
        provincias[provincia][ciudad].append({
            "fecha": fecha,
            "ruta": ruta_directorio,
            "num_archivos": len(archivos),
            "lat": lat,
            "lon": lon,
            "pais": pais
        })

    return provincias, cache

def generar_mapa_por_provincias():
    provincias, cache = agrupar_ciudades_por_provincia()

    # ---------------------------------------------------------
    # 1. Calcular centro del mapa
    # ---------------------------------------------------------
    coords = [
        (info["lat"], info["lon"])
        for info in cache.values()
        if isinstance(info, dict) and "lat" in info and "lon" in info
    ]

    if coords:
        lat_centro = sum(p[0] for p in coords) / len(coords)
        lon_centro = sum(p[1] for p in coords) / len(coords)
    else:
        lat_centro, lon_centro = 40.4167, -3.7033

    mapa = folium.Map(location=[lat_centro, lon_centro], zoom_start=5)

    # ---------------------------------------------------------
    # 2. Marcadores por provincia (uno por provincia)
    # ---------------------------------------------------------
    lista_provincias = list(provincias.keys())

    for provincia, ciudades in provincias.items():
        lat_list = []
        lon_list = []

        for ciudad, entradas in ciudades.items():
            for e in entradas:
                lat_list.append(e["lat"])
                lon_list.append(e["lon"])

        if not lat_list:
            continue

        lat_prov = sum(lat_list) / len(lat_list)
        lon_prov = sum(lon_list) / len(lon_list)

        popup_html = f"<b>{provincia}</b>"
        popup = folium.Popup(popup_html, max_width=250)

        folium.Marker(
            location=[lat_prov, lon_prov],
            popup=popup,
            tooltip=provincia,
            icon=folium.Icon(color="green", icon="info-sign", icon_color="#008000")
        ).add_to(mapa)

    # ---------------------------------------------------------
    # 3. Inyectar datos en JS
    # ---------------------------------------------------------
    mapa.get_root().html.add_child(
        folium.Element(
            "<script>window.provinciasData = " + json.dumps(provincias) + ";</script>"
        )
    )

    mapa.get_root().html.add_child(
        folium.Element(
            "<script>window.listaProvincias = " + json.dumps(lista_provincias) + ";</script>"
        )
    )

    # ---------------------------------------------------------
    # 4. JS principal
    # ---------------------------------------------------------
    mapa.get_root().html.add_child(folium.Element("""
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>

<script>

let bridge = null;

new QWebChannel(qt.webChannelTransport, function(channel) {
    bridge = channel.objects.bridge;
});

function obtenerMapaFolium() {
    return Object.values(window).find(v => v instanceof L.Map);
}

let intentos = 0;
function inicializarMapa() {
    window.mapInstance = obtenerMapaFolium();
    if (!window.mapInstance) {
        if (intentos++ < 20) setTimeout(inicializarMapa, 200);
        return;
    }
}
inicializarMapa();


// ===============================
//  MOSTRAR CIUDADES DE UNA PROVINCIA
// ===============================
function mostrarSelectorProvincia(provincia, lat, lon) {
    let ciudades = window.provinciasData[provincia];

    let html = `
        <div style="font-family:Segoe UI; width:260px;">
            <h3>${provincia}</h3>
            <p>Selecciona una ciudad:</p>
            <ul>
    `;


    for (let ciudad of Object.keys(ciudades).sort((a, b) => a.localeCompare(b))) {
        html += `
            <li>
                <a href="#" onclick="mostrarCiudad('${provincia}', '${ciudad}')">
                    ${ciudad} (${ciudades[ciudad].length} entradas)
                </a>
            </li>
        `;
    }

    html += `</ul></div>`;

    L.popup({maxWidth:300})
        .setLatLng([lat, lon])
        .setContent(html)
        .openOn(window.mapInstance);
}


// ===============================
//  MOSTRAR CARPETAS DE UNA CIUDAD
// ===============================
function mostrarCiudad(provincia, ciudad) {
    if (!window.mapInstance) return;
                                                  
    let data = window.provinciasData[provincia][ciudad];

    // ===============================
    // AGRUPAR POR AÑO
    // ===============================
    let grupos = {};

    for (let e of data) {
        let año = e.fecha.split("-")[0];
        if (!grupos[año]) grupos[año] = [];
        grupos[año].push(e);
    }

    // ===============================
    // ORDENAR CADA AÑO (más reciente primero)
    // ===============================
    for (let año in grupos) {
        grupos[año].sort((a, b) => b.fecha.localeCompare(a.fecha));
    }

    // ===============================
    // GENERAR HTML CON SCROLL
    // ===============================
    let html = `
        <div style="font-family:Segoe UI; width:260px; max-height:300px; overflow-y:auto; padding-right:10px;">
            <h3>${ciudad}</h3>
            <p>Carpetas encontradas:</p>
    `;

    for (let año of Object.keys(grupos).sort().reverse()) {
        html += `<h4 style="margin-bottom:4px; margin-top:12px;">${año}</h4>`;
        html += `<ul style="padding-left:0; list-style:none;">`;

        for (let e of grupos[año]) {
            let rutaEscapada = e.ruta.replace(/\\\\/g, '\\\\\\\\');

            html += `
                <li style="margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">
                    <div style="padding-left:12px;">
                        <b>${e.fecha}</b> (${e.num_archivos} archivos)
                    </div>

                    <div onclick="abrirCarpeta('${rutaEscapada}')"
                         style="cursor:pointer; padding-left:10px;">
                        <svg class="icono-ojo" width="22" height="22" viewBox="0 0 24 24">
                            <path d="M12 5c-7.633 0-11 7-11 7s3.367 7 11 7 11-7 11-7-3.367-7-11-7zm0 
                            12c-2.761 0-5-2.239-5-5s2.239-5 
                            5-5 5 2.239 5 5-2.239 5-5 5zm0-8c-1.654 
                            0-3 1.346-3 3s1.346 3 3 3 
                            3-1.346 3-3-1.346-3-3-3z"/>
                        </svg>
                    </div>
                </li>
            `;
        }

        html += `</ul>`;
    }

    html += `</div>`;

    // ===============================
    // MOSTRAR POPUP
    // ===============================
    L.popup({maxWidth:300})
        .setLatLng([data[0].lat, data[0].lon])
        .setContent(html)
        .openOn(window.mapInstance);
}


// ===============================
//  ABRIR CARPETA
// ===============================
function abrirCarpeta(ruta) {
    if (bridge) bridge.recibirRuta(ruta);
}

</script>

<style>
.icono-ojo path {
    fill: #2c3e50;
    transition: fill 0.2s ease;
}
.icono-ojo:hover path {
    fill: #007bff;
}
</style>
"""))

    # ---------------------------------------------------------
    # 5. CLIC DIRECTO EN MARCADORES DE PROVINCIA
    # ---------------------------------------------------------
    mapa.get_root().html.add_child(folium.Element("""
<script>
setTimeout(() => {
    const map = Object.values(window).find(v => v instanceof L.Map);
    if (!map) return;

    let indice = 0;

    map.eachLayer(function(layer) {
        if (layer instanceof L.Marker) {

            // Asignar provincia según el orden de creación
            layer._provincia = window.listaProvincias[indice];
            indice++;

            const lat = layer.getLatLng().lat;
            const lon = layer.getLatLng().lng;

            layer.on('click', function() {
                mostrarSelectorProvincia(layer._provincia, lat, lon);
            });
        }
    });
}, 600);
</script>
"""))
    
    texto_titulo = "MAPA DE PROVINCIAS" 

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
            border: 2px solid #008000; /* Borde verde a juego con tus marcadores */
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

    ruta_salida = get_ruta_mapa_provincias_html()
    mapa.save(ruta_salida)
