'''
Script en Python.
Para poder obtener el nombre completo necesario para la copia del mismo
    en el disco duro, utilizamos el parámetro 'GetDetailsOf', que nos muestra
    el nombre en crudo, incluyendo la extensión. Con esta extensión podremos 
    comprobar si se trata de una imagen o de un video.
'''
import os
import win32com.client
from copia_mtp import copiar_archivo_mtp
#from metadatos_video_mtp import obtener_gps_video

ruta = "C:\\FotosTemp"

def listar_archivos_mtp():
    shell = win32com.client.Dispatch("Shell.Application")
    este_equipo = shell.NameSpace(17)

    # 1. Buscar el móvil
    movil = next((i for i in este_equipo.Items() if "Galaxy A56 5G" in i.Name), None)
    if not movil:
        print("No se encontro ningún Movil.")
        return []
    
    try:
        # 2. Navegar hasta la carpeta Camera
        storage = movil.GetFolder.ParseName("Almacenamiento interno")
        if not storage: storage = movil.GetFolder.ParseName("Internal storage")

        dcim = storage.GetFolder.ParseName("DCIM")
        camera = dcim.GetFolder.ParseName("Camera")

        if not camera:
            return []
        
        # 3. Obtener todos los elementos y extraer sus nombre
        archivos = []
        # Guardamos la referencia al objeto folder
        folder_obj = camera.GetFolder
        for item in folder_obj.Items():
            # Filtramos para no incluir subcarpetas, solo archivos
            if not item.IsFolder:
                # Obtenemos el nombre completo, incluida la extensión.
                nombre_completo = folder_obj.GetDetailsOf(item, 0)
                archivos.append(nombre_completo)

        return archivos
    
    except Exception as e:
        print(f"Error al listar: {e}")
        return []
    
# Uso
lista_fotos = listar_archivos_mtp()
print(f"Se han encontrado {len(lista_fotos)} archivos.")
archivo = "VID_20250512_101613.mp4"
if archivo in lista_fotos:
    print(copiar_archivo_mtp(archivo, "C:\\FotosTemp"))
    #print(obtener_gps_video(os.path.join(f"{ruta}/{archivo}")))
    print("*" * 30)
