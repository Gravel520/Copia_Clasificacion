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
from folium.plugins import Search
from collections import defaultdict
from copia_clasificador_fotos import cargar_json_unico
from config_paths import get_ruta_mapa_html, get_ruta_principal, geocodificador, ruta_json_unico

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

def obtener_coordenadas(ciudad, pais):
    nombre_carpeta = f'{ciudad}, {pais}'
    try:
        location = geocodificador().geocode(nombre_carpeta, timeout=10)
        if location:
            return location.latitude, location.longitude
        
        else:
            print(f'No se encontró ubicación para: {nombre_carpeta}')
            return None
        
    except Exception as e:
        print(f'Error geolocalizando {nombre_carpeta}: {e}')
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
        <b>{ciudad}, {pais} - {fecha} ({num} archivos)</b><br>
        <button onclick="enviarRuta('{ruta}')">Ver archivos</button><br><br>
        """
    html += "</div>"
    return html    

def generar_mapa(features):
    # Inicializamos la localización inicial (Madrid, España).
    location = geocodificador().geocode('Madrid, España', timeout=10)
    mapa = folium.Map(location=[location.latitude, location.longitude], zoom_start=10)
    
    # Crear capa GeoJSON
    geojson_layer = folium.GeoJson(
        {"type": "FeatureCollection", "features": features},
        name="Fotos",
        popup=folium.GeoJsonPopup(fields=["popup"], labels=False),
        tooltip=folium.GeoJsonTooltip(fields=["nombre"])
    ).add_to(mapa)

    # Añadir buscador
    Search(
        layer=geojson_layer,
        search_label='nombre',
        placeholder='Buscar por ciudad, país o fecha',
        collapsed=False
    ).add_to(mapa)

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
        agrupadas[(ciudad, pais)].append((fecha, ruta_directorio, len(archivos)))

    features = []
    for (ciudad, pais), entradas in agrupadas.items():
        coordenadas = obtener_coordenadas(ciudad, pais)
        if not coordenadas:
            continue

        lat, lon = coordenadas
        html = crear_popup_html(ciudad, pais, entradas)
        feature = {
            "type": "Feature",
            "properties": {
                "nombre": f"{ciudad} {pais}",
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

    generar_mapa(features)
