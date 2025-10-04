'''
Script en Python.
Con este script vamos a crear un mapa con marcas de las fotos
existentes en distintos directorios.
Estas marcas pertenecerán a una fotográfia.
'''

import folium
import base64
import os
import webbrowser
import json
from PIL import Image

ruta_mapas = './modulo_folium/'
ruta_duplicados = './duplicados.json'

# Función para cargar el json con los datos de las fotos.
def cargar_json(ruta):
    if os.path.exists(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Función para crear el mapa con las marcas.
def crear_mapa(registros):
    mapa = folium.Map(
        location=[registros[0]['latitud'], registros[0]['longitud']], 
        zoom_start=8)
    
    for r in registros:
        # Añadimos marca con la imagen codificada en base64.
        with open(r['ruta'], 'rb') as img_file:
            encoded = base64.b64encode(img_file.read()).decode()

        # Crear el HTML con la imagen embebida y la fecha de la misma debajo.
        imagen_html = f"""
        <div style='text-align:center'>
            <img src='data:image/jpeg;base64, {encoded}' width='100' height='80'><br>
            <span style='font-size:8pt; color:#333'>{r['fecha']}</span>
        </div>
        """
        popup = folium.Popup(imagen_html, max_width=120)

        # Creamos la marca con la imagen.
        folium.Marker(
            location=[r['latitud'], r['longitud']],
            popup=popup,
            #popup=f"{r['ubicacion']} ({r['fecha']})",
            icon=folium.Icon(color='red', icon='camera')
        ).add_to(mapa)

    mapa.save(f'{ruta_mapas}mapa_historial.html')

# Función principal.
def main():
    # Cargamos los datos de los archivos a través de un json
    historial = cargar_json(ruta_duplicados)

    # Llamamos a la función para crear el mapa, como parámetro le mandamos
    #   los datos de los registros del json.
    crear_mapa(historial)

    # Abrimos automáticamente el mapa en el navegador.
    webbrowser.open(os.path.abspath(f'{ruta_mapas}mapa_historial.html'))    

# Ejecutamos el script.
if __name__ == '__main__':
    main()