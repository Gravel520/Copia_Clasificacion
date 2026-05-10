'''
Script en Python.
'''

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
)
from PyQt5 import QtWidgets
from config_paths import extensiones_validas

class VentanaCarpetas(QDialog):
    def __init__(self, datos_json, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Resumen de Carpetas")
        self.resize(600, 400)

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
        # No modificar, No resaltar y selección de filas enteras
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        self.tabla.setHorizontalHeaderLabels(["Ubicación", "Fecha", "Cantidad"])

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

class VentanaCarpetasVideo(QDialog):
    def __init__(self, datos_json, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Carpetas con Archivos de Vídeo")
        self.resize(600, 400)

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
        self.tabla.setHorizontalHeaderLabels(["Ruta de la Carpeta", "Cantidad"])

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
