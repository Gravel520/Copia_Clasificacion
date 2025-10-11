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

ruta_mapas = './PyQt/mapas'
ruta_principal = 'E:/BackupFotos'

# Iniciamos el geocodificador.
geolocator = Nominatim(user_agent="copilot-mapa")

# Función para obtener la lista de los directorios de la ruta principal.

directorios = os.listdir(ruta_principal)

# Inicializamos la localización inicial (Madrid, España).
location = geolocator.geocode('Madrid, España', timeout=10)

# Creamos un mapa centrado en España (Madrid).
mapa = folium.Map(location=[location.latitude, location.longitude], zoom_start=10)

# Función para extraer el nombre de la ciudad.
def extraer_ciudad(nombre):
    ciudad = nombre.split(')')[0][1:]
    pais = nombre.split(')')[1][1:]
    fecha = nombre.split(')')[2][1:]
    return ciudad, pais, fecha

for directorio in directorios:
    archivos = os.listdir(f'{ruta_principal}/{directorio}')
    numero = len(archivos)

    ciudad = extraer_ciudad(directorio)

    nombre_carpeta = f'{ciudad[0]}, {ciudad[1]}'
    location = geolocator.geocode(nombre_carpeta, timeout=10)

    # HTML con botón que llama a PyQt
    html = f"""
    <div style="width:250px;" data-directorio="{ruta_principal}/{directorio}">
    <b>{nombre_carpeta} - {numero} archivos</b><br>
    <button onclick="enviarRuta('{ruta_principal}/{directorio}')">Ver archivos</button>
    </div>
    """

    popup = folium.Popup(folium.Html(html, script=True), max_width=300)

    folium.Marker(
        [location.latitude, location.longitude],
        popup=popup
    ).add_to(mapa)
    time.sleep(1) # Esperamos 1 segundo para dar tiempo al geolocalizador.

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

mapa.save(f'{ruta_mapas}mapa_fotos.html')
