'''
Script en Python.
'''

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
)
from PyQt5 import QtWidgets
from config_paths import extensiones_validas, meses, get_ruta_principal
from componentes.video_player_vlc import VideoPlayer
from config_manager import settings

class VentanaCarpetas(QDialog):
    def __init__(self, datos_json, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Resumen de Carpetas")
        self.resize(600, 400)

        self.vp = None

        layout = QVBoxLayout(self)

        # 1. Procesar los datos (Agrupar y Contar)
        resumen = {}
        items = datos_json.get("clasificados", {}).get("items", [])

        for item in items:
            # Creamos una clave única combinando ubicación y fecha
            clave = (item['ubicacion'], item['fecha'])
            resumen[clave] = resumen.get(clave, 0) + 1

        # 2. Configurar la tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        # No modificar y selección de filas enteras
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.tabla.setHorizontalHeaderLabels(["Ubicación", "Fecha", "Cantidad"])

        # Señal de la tabla.
        self.tabla.cellDoubleClicked.connect(lambda row, col: self.abrir_visor(row, col))

        # Ajustar columnas para que ocupen el espacion
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Interactive)

        # 3. Llenar la tabla con los datos agrupados
        self.tabla.setRowCount(len(resumen))

        for fila, ((ubicacion, fecha), cantidad) in enumerate(resumen.items()):
            self.tabla.setItem(fila, 0, QTableWidgetItem(ubicacion))
            self.tabla.setItem(fila, 1, QTableWidgetItem(fecha))
            # Usamos setData para que al ordenar la tabla reconozca números y no texto
            item_cantidad = QTableWidgetItem()
            item_cantidad.setData(0, cantidad)
            self.tabla.setItem(fila, 2, item_cantidad)

        self.tabla.setSortingEnabled(True) # Permitir ordenar al hacer clic
        layout.addWidget(self.tabla)

    def abrir_visor(self, row, column):
        # Preparamos los parámtros para el visor.
        # Ubicación más la fecha.
        carpeta = self.tabla.item(row, 0).text()
        fecha_ruta = self.tabla.item(row, 1).text()
        
        # Completamos la ruta de visualización desde la principal.
        ruta = os.path.normpath(os.path.join(get_ruta_principal(), f'{carpeta}{fecha_ruta}'))

        # Obtenemos los archivos y seleccionamos el primero.
        archivos = os.listdir(f'{ruta}')
        archivo = os.path.normpath(os.path.join(ruta, archivos[0]))

        # Creamos los datos del més, en letra, y el año.
        datos = f'{meses()[int(fecha_ruta[6:8]) - 1]} del {fecha_ruta[1:5]}'

        # Si hay un reproductor abierto lo cerramos
        if self.vp is not None:
            self.vp.close()
            self.vp = None

        # Creamos uno nuevo, pasándole como parámetros la ruta completa
        #   de los archivos que hay que visualizar, la ruta del primer
        #   archivo para que nos podamos mover adelante y atras, y los
        #   datos para la etiqueta de la fecha. El parámetro de 'solo_video'
        #   no se pasa porque se visualizan todos los archivos de la carpeta.
        self.vp = VideoPlayer(ruta, archivo, datos)
        self.vp.show()
        
class VentanaCarpetasVideo(QDialog):
    def __init__(self, datos_json, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Carpetas con Archivos de Vídeo")
        self.resize(600, 400)

        self.vp = None

        layout = QVBoxLayout(self)

        # 1. Procesar datos: Filtrar por vídeo y agrupar por carpetas
        resumen_video = {}
        items = datos_json.get("clasificados", {}).get("items", [])

        for item in items:
            ruta = item.get('ruta', '')
            if ruta.lower().endswith(extensiones_validas("video")):
                # Extraemos la carpeta de la ruta completa
                carpeta = os.path.dirname(ruta)
                carpeta = os.path.basename(carpeta)
                resumen_video[carpeta] = resumen_video.get(carpeta, 0) + 1

        # 3. Configurar la Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(2)
        self.tabla.setHorizontalHeaderLabels(["Ubicación y Fecha", "Cantidad"])
        self.tabla.cellDoubleClicked.connect(lambda row, col: self.abrir_visor_video(row, col))

        # Bloquear edición y selección
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setAlternatingRowColors(True)

        # Ajuste de columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        # 4. Llenar la tabla
        self.tabla.setRowCount(len(resumen_video))
        for fila, (ruta_carpeta, cantidad) in enumerate(resumen_video.items()):
            self.tabla.setItem(fila, 0, QTableWidgetItem(ruta_carpeta))

            item_cantidad = QTableWidgetItem()
            item_cantidad.setData(0, cantidad)
            self.tabla.setItem(fila, 1, item_cantidad)

        self.tabla.setSortingEnabled(True)
        layout.addWidget(self.tabla)

    def abrir_visor_video(self, row, column):
        # 1. Preparamos los datos para el reproductor, para
        #   pasarlos como parámetros.
        # La ruta desde 'BackupFotos' y la fecha.
        ruta = self.tabla.item(row, 0).text()
        fecha = (ruta).split(')')[2][1:]

        # 2. Creamos la ruta completa desde la principal
        ruta = os.path.join(get_ruta_principal(), ruta)

        # 3. Obtenemos, sólamente, los archivos de video
        archivos = [
            f for f in os.listdir(ruta)
            if f.lower().endswith(extensiones_validas("video"))
        ]

        # 4. Seleccionamos el primer archivo de la lista para
        #   pasarlo como parámetro.
        archivo = f'{ruta}/{archivos[0]}'

        # 5. El més, en letra, junto con el año también como parámetro.
        datos = f'{meses()[int(fecha[5:]) - 1]} del {fecha[0:4]}'

        # Si hay un reproductor abierto lo cerramos
        if self.vp is not None:
            self.vp.close()
            self.vp = None

        # Creamos uno nuevo, junto con los parámetros obtenidos.
        #   El 'True' es para que se visualicen sólo los videos.
        self.vp = VideoPlayer(ruta, archivo, datos, True)
        self.vp.show()
        