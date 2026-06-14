'''
Script en Python.
'''

def generar_reporte(resultados):
    """
    resultados: lista de dicts con:
        {
        "nombre": "Nombre del chequeo",
        "problemas": [...]
        }
    """
    resumen = []

    for r in resultados:
        nombre = r.get("nombre")
        problemas = r.get("problemas", [])
        resumen.append({
            "chequeo": nombre,
            "total_problemas": len(problemas),
            "detalle": problemas
        })

    return resumen
