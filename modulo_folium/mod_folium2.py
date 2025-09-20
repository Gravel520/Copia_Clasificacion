'''
Script en Python.
Folium es una potente biblioteca de Python que permite crear mapas
interactivos aprovechando las ventanas de la biblioteca Leaflet de
JavaScript. Es especialmente útil para visualizar datos geoespaciales
y permite crear diversos tipos de mapas, incluyendo mapas coropletas,
que colorean unidades geográficas según valores agregados.
'''

import folium
import pandas as pd

ruta_mapas = './modulo_folium/'

'''
Un mapa de coropletas es un tipo de mapa en el que las áreas están 
sombreadas o con patrones en proporción al valor de una variable. Este
código crea un mapa de coropletas que muestra la huella ecológica per
cápita de varios países.
'''
def mapa_coropletas():
    # Obtenemos los datos.
    data = pd.read_csv(f'{ruta_mapas}footprint.csv')

    # Obtenemos la capa GeoJSON.
    geojson_url = "http://geojson.xyz/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson"

    # Creamos el mapa.
    m = folium.Map(location=[30, 10], zoom_start=3)

    # Añadimos la capa coropleta.
    folium.Choropleth(
        geo_data=geojson_url,
        data=data,
        columns=["Country", "Total Ecological Footprint"],
        key_on='feature.properties.name',
        fill_color='YlGn',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='Huella ecológica per cápita'
    ).add_to(m)

    # Guardamos el mapa.
    m.save(f'{ruta_mapas}coropletas_mapa.html')

'''
Folium ofrece varias opciones para personalizar la apariencia y el 
comportamiento del mapa. Por ejemplo se puede cambiar el estilo de mosaico,
ajustar el nivel de zoom y agregar marcadores o ventanas emergentes.
Este código crea un mapa con el estilo de mosaico 'Stamen Terrain' y 
agrega un marcador con una ventana emergente.
'''
def mapa_customizado():
    # Crear el mapa con un estilo de mosaico diferente.
    m = folium.Map(location=[40.28419, -3.79415], 
                   zoom_start=10,
                   tiles='OpenStreetMap')
    
    # Añadir el marcador con la ventana emergente.
    folium.Marker(
        location=[40.28419, -3.79415],
        popup='Fuenlabrada, Madrid',
        icon=folium.Icon(icon='cloud')
    ).add_to(m)

    # Guardar el mapa.
    m.save(f'{ruta_mapas}customizado_mapa.html')

#mapa_coropletas()

mapa_customizado()