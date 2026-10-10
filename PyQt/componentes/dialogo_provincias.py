'''
Script en Python.
'''

import json
import requests
import re

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLabel, QLineEdit, QAbstractItemView,
    QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from utils.utils_cache import cargar_cache, guardar_cache, normalizar_texto
from utils.utils_provincias import NominatimExtractor, DistritoPostal
from config_paths import PROVINCIAS_ES, PROVINCIAS_FR, PROVINCIAS_PT
from componentes.controles import DialogoCargando

COLOR_FALTA = QColor(255, 200, 200)

# ---------------------------------------------------------
# Diálogo para editar un registro
# ---------------------------------------------------------
class DialogoEditar(QDialog):
    def __init__(self, clave, datos, ruta_json, parent=None):
        super().__init__(parent)
        self.clave = clave
        self.datos = datos
        self.pais = datos.get("pais", "")
        self.ruta_json = ruta_json

        # Crear extractor con el diccionario de provincias según el país.
        if self.pais == "Espana":
            mapa_provincias = PROVINCIAS_ES
        elif self.pais == "Francia":
            mapa_provincias = PROVINCIAS_FR
        elif self.pais == "Portugal":
            mapa_provincias = PROVINCIAS_PT

        self.extractor = NominatimExtractor(mapa_provincias)

        self.setWindowTitle(f"Modificar: {clave}")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Provincia
        layout.addWidget(QLabel("Provincia:"))
        self.input_provincia = QLineEdit(datos.get("provincia", ""))
        layout.addWidget(self.input_provincia)

        # Postal
        layout.addWidget(QLabel("Código Postal:"))
        self.input_postal = QLineEdit(datos.get("postal", ""))
        layout.addWidget(self.input_postal)

        # Botones
        btn_layout = QHBoxLayout()

        btn_auto = QPushButton("Autocompletar (nominatim)")
        btn_auto.clicked.connect(self.obtener_postal_nominatim)
        btn_layout.addWidget(btn_auto)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self.guardar)
        btn_layout.addWidget(btn_guardar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancelar)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # ---------------------------------------------------------
    # Autocompletar usando Nominatim
    # ---------------------------------------------------------
    def extraer_ciudad_provincia(self):
        lat = self.datos["lat"]
        lon = self.datos["lon"]
        if lat is None or lon is None:
            return "", ""

        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"

        try:
            r = requests.get(url, headers={"User-Agent": "Copia_Clasificacion"})
            info = r.json()
            # Ciudad: intentar varios campos habituales
            address = info.get("address", {}) if isinstance(info, dict) else {}
            ciudad = address.get("city") or address.get("town") or address.get("village") or address.get("municipality") or ""

            
            # usar extractor para postal y provincia
            postal, provincia = self.extractor.extract(info)

            return ciudad, provincia
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo obtener información.\n{e}")
            return "", ""
        
    def obtener_postal_nominatim(self):
        dlg = DialogoCargando("Completando información...", self)
        dlg.show()
        QApplication.processEvents()
       
        ciudad = self.datos.get("ciudad", "")
        provincia = self.datos.get("provincia", "")

        if ciudad == "" or provincia == "":
            ciudad, provincia =self.extraer_ciudad_provincia()        

        ciudad = normalizar_texto(ciudad)
        provincia = normalizar_texto(provincia)
        postal = DistritoPostal.buscar_cp_directo(ciudad, provincia, self.pais)

        if postal:
            self.input_postal.setText(postal)
            self.datos["postal"] = postal

        if provincia:
            self.input_provincia.setText(normalizar_texto(provincia))
            self.datos["provincia"] = provincia

        dlg.close()

    def extraer_postal_display_name(self, display_name):
        m = re.search(r"\b(\d{5})\b", display_name)
        if m:
            return m.group(1)
        return ""

    # ---------------------------------------------------------
    # Guardar cambios
    # ---------------------------------------------------------
    def guardar(self):
        postal = self.input_postal.text().strip()
        provincia = self.input_provincia.text().strip()

        if not provincia:
            QMessageBox.warning(self, "Error", "La provincia no puede estar vacía.")
            return

        data = cargar_cache()
        data[self.clave]["postal"] = postal
        data[self.clave]["provincia"] = provincia

        guardar_cache(data)

        QMessageBox.information(self, "Guardado", "Registro actualizado correctamente.")
        self.accept()

# ---------------------------------------------------------
# Diálogo principal: lista y estado
# ---------------------------------------------------------
class DialogoProvincias(QDialog):
    def __init__(self, ruta_json, parent=None):
        super().__init__(parent)
        self.ruta_json = ruta_json

        self.setWindowTitle("Comprobación de Provincias")
        self.setMinimumWidth(400)
        self.setMaximumHeight(600)

        layout = QVBoxLayout()

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Clave", "Ciudad", "Provincia", "Postal", "País", "Estado"])
        self.tabla.setStyleSheet("""
        QTableWidget::item:selected {
            background-color: #3874f2;
            border: none;
            color: white;
        }
        """)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Hacer click en una celda y que se ponga toda la fila azul
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SingleSelection)

        # Doble click -> editar
        self.tabla.itemDoubleClicked.connect(self.editar_registro)

        layout.addWidget(self.tabla)

        # Botón refrescar
        btn_refrescar = QPushButton("Refrescar")
        btn_refrescar.clicked.connect(self.cargar_datos)
        layout.addWidget(btn_refrescar)

        self.setLayout(layout)
        self.cargar_datos()

    # ---------------------------------------------------------
    # Cargar datos en la tabla
    # ---------------------------------------------------------
    def cargar_datos(self):
        data = cargar_cache()

        self.tabla.setRowCount(len(data))

        for fila, (clave, info) in enumerate(data.items()):
            ciudad = info.get("ciudad", "")
            provincia = info.get("provincia", "")
            postal = info.get("postal", "")
            pais = info.get("pais", "")
            
            estado = "OK"
            if not provincia or not postal or not ciudad:
                estado = "Falta información"

            # Insertar datos
            self.tabla.setItem(fila, 0, QTableWidgetItem(clave))
            self.tabla.setItem(fila, 1, QTableWidgetItem(ciudad))
            self.tabla.setItem(fila, 2, QTableWidgetItem(provincia))
            self.tabla.setItem(fila, 3, QTableWidgetItem(postal))
            self.tabla.setItem(fila, 4, QTableWidgetItem(pais))
            self.tabla.setItem(fila, 5, QTableWidgetItem(estado))

            # Cambiar el color según el estado
            if estado == "Falta información":                
                for col in range(self.tabla.columnCount()):
                    self.tabla.item(fila, col).setBackground(COLOR_FALTA)

            self.ajustar_tamano_dialogo()

    # ---------------------------------------------------------
    # Abrir diálogo de edición
    # ---------------------------------------------------------
    def editar_registro(self, item):
        fila = item.row()
        clave = self.tabla.item(fila, 0).text()

        data = cargar_cache()
        datos = data[clave]

        dlg = DialogoEditar(clave, datos, self.ruta_json, self)
        dlg.exec_()

        self.cargar_datos()

    def ajustar_tamano_dialogo(self):
        # Ajustar columnas y filas al contenido
        self.tabla.resizeColumnsToContents()
        self.tabla.resizeRowsToContents()

        # Calcular ancho total de columnas
        ancho_total = sum(self.tabla.columnWidth(c) for c in range(self.tabla.columnCount()))

        # Añadir ancho del header vertical + márgenes
        ancho_total += self.tabla.verticalHeader().width() + 60

        # Calcular alto total de filas
        alto_total = sum(self.tabla.rowHeight(r) for r in range(self.tabla.rowCount()))

        # Añadir alto del header horizontal + márgenes
        alto_total += self.tabla.horizontalHeader().height() + 60

        # Redimensionar el diálogo
        self.resize(ancho_total, alto_total)
