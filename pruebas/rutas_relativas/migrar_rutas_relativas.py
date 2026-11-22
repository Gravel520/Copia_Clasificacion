'''
Script para convertir las rutas absolutoas en relativas
    de archivo 'archivos_unificados.json'

    Pasaríamos de esto:
    "C:\\\\Users\\\\katal\\\\Pictures\\BackupFotos\\(Manzanares el Real)(Espana)(2026-04)\\20260401_120748.jpg"
    
    a esto:
    "(Manzanares el Real)(Espana)(2026-04)\\20260401_120748.jpg"

    De esta forma podremos exportar estos datos a otro pc sin necesidad de volver a generar
        las nuevas rutas. Solo haría falta concatenar la ruta principal de la aplicación,
        más la ruta relativa de cada archivo.

    Esta es la ruta principal de la aplicación de este ordenador:
    "C:\\\\Users\\\\katal\\\\Pictures\\BackupFotos\\"
'''

import json
from pathlib import Path

DIRECTORIO_ACTUAL = Path(__file__).parent
RUTA_JSON = DIRECTORIO_ACTUAL / "archivos_unificados.json"

# 1. Cargar el archivo json
with open(RUTA_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. Definir la ruta base
ruta_principal = Path(r"C://Users/katal/Pictures/BackupFotos")

# 3. Iterar en la estructura correcta del json
for i, item in enumerate(data["clasificados"]["items"], start=1):
    # Convertimos a objeto Path para operar y calculamos la ruta relativa
    ruta_absoluta = Path(item["ruta"])
    ruta_relativa = ruta_absoluta.relative_to(ruta_principal)

    # Guardamos el resultado como texto (string) en formato Windows
    item["ruta"] = str(ruta_relativa)
    print(f'{i} - {item["ruta"]}')

# 4. Guardar el json
with open(RUTA_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
