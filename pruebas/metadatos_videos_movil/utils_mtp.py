'''

'''

import win32com.client
import os
import time

def buscar_movil():
    shell = win32com.client.Dispatch("Shell.Application")
    este_equipo = shell.NameSpace(17)

    # 1. Buscar el móvil
    movil = next((i for i in este_equipo.Items() if "Galaxy A56 5G" in i.Name), None)
    return movil, shell

def listar_archivos_mtp():
    movil, shell = buscar_movil()

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
        for item in camera.GetFolder.Items():
            # Filtramos para no incluir subcarpetas, solo archivos
            if not item.IsFolder:
                archivos.append(item.Name)

        return archivos
    
    except Exception as e:
        print(f"Error al listar: {e}")
        return []

def copiar_archivo_mtp(nombre_archivo, carpeta_destino_pc):
    movil, shell = buscar_movil()

    if not movil:
        return "❌ No se encontró el Galaxy A56 5G en 'Este equipo'"

    try:
        # 2. IMPORTANTE: Usamos 'movil.GetFolder' (No dispositivo)
        storage = movil.GetFolder.ParseName("Almacenamiento interno")
        
        # Si tu Windows está en inglés, podría ser "Internal storage"
        if not storage:
            storage = movil.GetFolder.ParseName("Internal storage")
            
        if not storage:
            return "❌ No se pudo acceder al 'Almacenamiento interno'. ¿Está el móvil desbloqueado?"

        # 3. Navegamos por el resto de carpetas
        dcim = storage.GetFolder.ParseName("DCIM")
        camera = dcim.GetFolder.ParseName("Camera")
        
        if not camera:
            return "❌ No se encontró la carpeta DCIM/Camera"

        archivo_movil = camera.GetFolder.ParseName(nombre_archivo)
        
        if archivo_movil:
            # Aseguramos que la carpeta destino exista
            if not os.path.exists(carpeta_destino_pc):
                os.makedirs(carpeta_destino_pc)
                
            destino = shell.NameSpace(os.path.abspath(carpeta_destino_pc))
            
            # Copiamos (16 = Sobrescribir, 1024 = No mostrar errores de Windows)
            destino.CopyHere(archivo_movil, 16)
            
            # MTP es lento, damos un segundo para que Windows termine de soltar el archivo
            time.sleep(1) 
            
            return f"✅ Copiado con éxito (MTP + GPS): {nombre_archivo}"
        else:
            return f"❌ El archivo {nombre_archivo} no existe en la carpeta Camera"
            
    except Exception as e:
        return f"☠ Error navegando en MTP: {str(e)}"
