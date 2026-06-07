'''

'''

from PyQt5.QtCore import QThread, QObject, pyqtSignal

class MapaGruposWorker(QObject):
    """
    Clase para procesar la lógica pesada de creación del mapa de grupos.

    Esta clase hereda de `QObject` y tiene dos señales definidas: `finalizado` y `error`.
    `finalizado` se emite cuando se ha procesado correctamente el mapa de grupos y emite el resultado.
    `error` se emite cuando ocurre un error durante el procesado del mapa.

    Args:
        gestor_instancia (Gestor): Instancia del gestor que maneja la lógica del mapa.
        fotos_json (dict): Diccionario de JSON con información de las fotos.
        salida (str): Ruta de salida donde se guardará el mapa.

    Methods:
        procesar(): Procesa la lógica pesada de creación del mapa de grupos.
    """

    finalizado = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, gestor_instancia, fotos_json, salida):
        super().__init__()
        self.gestor = gestor_instancia
        self.fotos_json = fotos_json
        self.salida = salida

    def procesar(self):
        """
        Procesa la lógica pesada de creación del mapa de grupos.

        Llama a la lógica de generación del mapa de grupos y emite la señal `finalizado` con el resultado,
        o emite la señal `error` si no se encontraron grupos con fotos coincidentes.

        Raises:
            Exception: Si ocurre un error durante el procesado del mapa.
        """
        try:
            resultado = self.gestor.generar_mapa_todos_los_grupos_logica(self.fotos_json, self.salida)

            if resultado:
                self.finalizado.emit(resultado)
            else:
                self.error.emit("Ningún grupo tiene fotos coincidentes.")
        except Exception as e:
            self.error.emit(str(e))
            