'''
Script en Python.
Es una prueba para poder obtener la fecha de la fotografía.
el nombre del tag no es 'DateTimeOriginal', sino que es un número,
el 34853 en el orden 29.
Aqui obtengo la fecha a través de ese id y la convierto en el formato
que a mí me interesa.
'''

from PIL import Image
from datetime import datetime

# Ruta de la imagen
imagen_path = 'C:/BackupFotos/Cáceres_España_2025-02/IMG_20250214_105750.jpg'

# Abrir imagen y extraer EXIF
imagen = Image.open(imagen_path)
exif_data = imagen._getexif()

for tag_id, valor in exif_data.items():
    if tag_id == 34853:
        fecha_exif = datetime.strptime(exif_data[34853][29], "%Y:%m:%d")
        fecha = fecha_exif.strftime('%d_%m_%Y')
        print(f'Fecha: {fecha}')
