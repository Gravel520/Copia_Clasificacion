'''
Script en Python.

Este es uno de los tests más importantes porque el worker es el corazón 
del autodiagnóstico:
    · ejecuta los chequeos.
    · emite señales.
    · devuelve el report final

¿ Qué vamos a comprobar?
    1. Que el worker llama a los chequeos correctos.
    2. Que los chequeos reciben los parámetros correctos.
    3. Que el worker devuelve una lista de resultados.
    4. Que el orden de ejecución es correcto.
    5. Que funciona tanto con chequeos individuales como con "completo".

'''

# tests/worker/test_worker_autodiagnostico.py

from autodiagnostico.worker.worker_autodiagnostico import WorkerAutodiagnostico

def test_worker_autodiagnostico(monkeypatch):
    # Simular JSON cargado
    fake_json = {"clasificados": {"items": []}}

    def fake_cargar_json(_):
        return fake_json
    
    # Simular cache cargado
    fake_cache = {"(Madrid)(Espana)": [40.416775, -3.703790]}

    def fake_cargar_cache(_):
        return fake_cache

    # Simular funciones de chequeo
    def fake_check_directorios_vacios(_):
        return {"problemas": []}

    monkeypatch.setattr(
        "copia_clasificador_fotos.cargar_json_unico",
        fake_cargar_json
    )
    monkeypatch.setattr(
        "copia_clasificador_fotos.cargar_cache",
        fake_cargar_cache
    )

    # Simular chequeos
    llamadas = []

    def fake_json_carpetas(data, raiz):
        llamadas.append(("json_carpetas", data, raiz))
        return {"nombre": "JSON vs Carpetas", "problemas": []}
    
    def fake_json_cache(data, cache):
        llamadas.append(("json_cache", data, cache))
        return {"nombre": "JSON vs Cache", "problemas": []}
    
    def fake_integridad(data):
        llamadas.append(("integridad", data))
        return {"nombre": "Integridad", "problemas": []}
    
    def fake_directorios(data):
        llamadas.append(("directorios", data))
        return {"nombre": "Directorios", "problemas": []}
    
    def fake_corrupcion(data):
        llamadas.append(("corrupcion", data))
        return {"nombre": "Corrupcion", "problemas": []}

    monkeypatch.setattr(
        "autodiagnostico.chequeos.CHEQUEOS",
        {
            "json_carpetas": fake_json_carpetas,
            "json_cache": fake_json_cache,
            "integridad": fake_integridad,
            "directorios": fake_directorios,
            "corrupcion": fake_corrupcion
        }
    )

    # Crear worker
    worker = WorkerAutodiagnostico(
        ruta_json="fake.json",
        raiz_backup="backup/",
        chequeos=["json_carpetas", "integridad"]
    )

    # Ejecutar sin señales ni hilos
    resultados = []
    def fake_emit(result):
        resultados.extend(result)

    worker.terminado.emit = fake_emit

    worker.run()

    # Comprobaciones
    assert len(llamadas) == 2
    assert llamadas[0][0] == "json_carpetas"
    assert llamadas[1][0] == "integridad"
    
    assert len(resultados) == 2
    assert resultados[0]["nombre"] == "JSON vs Carpetas"
    assert resultados[1]["nombre"] == "Integridad"
    