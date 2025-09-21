'''
Script en Python.
Folium es una potente biblioteca de Python que permite crear mapas
interactivos aprovechando las ventanas de la biblioteca Leaflet de
JavaScript. Es especialmente útil para visualizar datos geoespaciales
y permite crear diversos tipos de mapas, incluyendo mapas coropletas,
que colorean unidades geográficas según valores agregados.
'''

import folium

ruta_mapas = './modulo_folium/'

'''
El siguiente código crea un mapa centrado en la latitud y longitud
especificadas y lo guarda como un archivo HTML.
'''
def mapa_simple():
    # Crear el mapa centrado en la localización especificada.
    latitud = 37.86203611111111
    longitud = -25.796530555555556
    m = folium.Map(location=[latitud, longitud], zoom_start=10)

    # Añadir marca.
    folium.Marker([latitud, longitud], popup="Vacaciones").add_to(m)

    # Se guarda el mapa en un archivo HTML.
    m.save(f'{ruta_mapas}mi_primer_mapa.html')


'''
Folium le permite agregar varias capas y datos a su mapa. Por ejemplo,
puede agregar una capa GeoJSON para mostrar los límites geográficos.
El siguiente ejemplo agregar una capa que representa los límites de los
paises al mapa.
'''
def mapa_limites_paises():
    # URL de GeoJSON, de donde obtener la capa.
    geojson_url = "http://geojson.xyz/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"

    # Crear el mapa
    m = folium.Map(location=[30, 10], zoom_start=3) 

    # Añadir la capa de GeoJSON.
    folium.GeoJson(geojson_url).add_to(m)

    # Guardar el mapa
    m.save(f'{ruta_mapas}mapa_con_geojson.html')

mapa_simple()

#mapa_limites_paises()