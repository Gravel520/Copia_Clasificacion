'''

'''
import win32com.client

def listar_nombres_mtp():
    shell = win32com.client.Dispatch("Shell.Application")
    este_equipo = shell.NameSpace(17)
    
    print("--- Dispositivos encontrados ---")
    for dispositivo in este_equipo.Items():
        print(f"Dispositivo: '{dispositivo.Name}'")
        if dispositivo.IsFolder:
            try:
                for sub in dispositivo.GetFolder.Items():
                    print(f"  Carpeta: '{sub.Name}'")
            except: pass

listar_nombres_mtp()
