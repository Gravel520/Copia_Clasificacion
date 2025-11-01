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
from geopy.geocoders import Nominatim
from folium.plugins import Search
from collections import defaultdict
from copia_clasificador_fotos import cargar_json

RUTA_MAPAS = './PyQt/mapas/'
RUTA_PRINCIPAL = 'E:/BackupFotos/'
GEOCODIFICADOR = Nominatim(user_agent="copilot-mapa")
HISTORIAL = './duplicados.json'

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
        location = GEOCODIFICADOR.geocode(nombre_carpeta, timeout=10)
        if location:
            return location.latitude, location.longitude
        
        else:
            print(f'No se encontró ubicación para: {nombre_carpeta}')
            return None
        
    except Exception as e:
        print(f'Error geolocalizando {nombre_carpeta}: {e}')
        return None
    
def crear_popup_html(ciudad, pais, entradas):
    html = f"<div style='width:250px;'>"
    for fecha, ruta, num in entradas:
        html += f"""
        <b>{ciudad}, {pais} - {fecha} ({num} archivos)</b><br>
        <button onclick="enviarRuta('{ruta}')">Ver archivos</button><br><br>
        """
    html += "</div>"
    return html
    
def crear_feature(ciudad, pais, fecha, ruta_directorio, numero_archivos, lat, lon):
    # HTML con botón que llama a PyQt
    html = f"""
    <div style="width:250px;" data-directorio="{ruta_directorio}">
    <b>{ciudad}, {pais} - {numero_archivos} archivos</b><br>
    <button onclick="enviarRuta('{ruta_directorio}')">Ver archivos</button>
    </div>
    """
    return {
        "type": "Feature",
        "properties": {
            "nombre": f"{ciudad} {pais} {fecha}",
            "popup": html
        },
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        }
    }

def generar_mapa(features):
    # Inicializamos la localización inicial (Madrid, España).
    location = GEOCODIFICADOR.geocode('Madrid, España', timeout=10)
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
    
    mapa.save(f'{RUTA_MAPAS}mapa_fotos.html')
    print("Mapa guardado en: ", f'{RUTA_MAPAS}mapa_fotos.html')

def main():
    '''
    Utilizamos el json 'duplicados' que es el historial de los 
    archivos que se van clasificando, porque en el vamos guardando
    los datos de las ubicaciones de los archivos si han sido 
    movidos o borrados.
    '''
    historial = cargar_json(HISTORIAL)

    agrupadas = defaultdict(list)
    combinaciones_unicas = set()

    for item in historial:
        clave = item['ubicacion'] + item['fecha']
        combinaciones_unicas.add(clave)

    for directorio in combinaciones_unicas:
        ruta_directorio = os.path.join(RUTA_PRINCIPAL, directorio)
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

    generar_mapa(features)

if __name__ == "__main__":
    main()
