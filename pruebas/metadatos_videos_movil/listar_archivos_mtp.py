'''

'''
import win32com.client
from copia_mtp import copiar_archivo_mtp

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
        for item in camera.GetFolder.Items():
            # Filtramos para no incluir subcarpetas, solo archivos
            if not item.IsFolder:
                archivos.append(item.Name)

        return archivos
    
    except Exception as e:
        print(f"Error al listar: {e}")
        return []
    
# Uso
lista_fotos = listar_archivos_mtp()
print(f"Se han encontrado {len(lista_fotos)} archivos.")
for archivo in lista_fotos[:5]:
    copiar_archivo_mtp(archivo, "C:\\FotosTemp")
