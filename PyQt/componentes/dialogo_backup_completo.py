'''
Script en Python.
'''

import sys

from pathlib import Path

from PyQt5.QtWidgets import (QDialog, QLabel, QPushButton, QFileDialog,
                             QVBoxLayout, QHBoxLayout, QProgressBar,
                             QMessageBox)

from PyQt5.QtCore import pyqtSignal

from copia_clasificador_fotos import cargar_json_unico

from config_paths import ruta_json_unico


class DialogoTransferencia(QDialog):
    exportarSolicitado = pyqtSignal(str)
    importarSolicitado = pyqtSignal(str)
    cancelarSolicitado = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle("Transferencia Biblioteca")

        self.resize(450, 180)

        layout = QVBoxLayout(self)

        css_style = """
            QLabel {
                font-size: 11pt;
                color: #2c3e50;
                font-weight: bold;
            }
        """

        self.lbl_estado = QLabel("Esperando...")
        self.lbl_estado.setStyleSheet(css_style)
        self.lbl_archivo = QLabel("")
        #self.lbl_archivo.setStyleSheet(css_style)
        self.lbl_tiempo = QLabel("Tiempo restante: --:--")
        self.lbl_tiempo.setStyleSheet(css_style)

        self.barra_metadatos = QProgressBar()
        self.barra_miniaturas = QProgressBar()
        self.barra_fotos = QProgressBar()
        self.barra_compresion = QProgressBar()

        layout.addWidget(self.lbl_estado)

        layout.addWidget(QLabel("Metadatos"))
        layout.addWidget(self.barra_metadatos)

        layout.addWidget(QLabel("Miniaturas"))
        layout.addWidget(self.barra_miniaturas)

        layout.addWidget(QLabel("Carpetas/archivos"))
        layout.addWidget(self.barra_fotos)

        layout.addWidget(QLabel("Compresión / Descompresión"))
        layout.addWidget(self.barra_compresion)

        layout.addWidget(self.lbl_tiempo)
        layout.addWidget(self.lbl_archivo)

        self.btn_exportar = QPushButton("Exportar")
        self.btn_importar = QPushButton("Importar")
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cerrar = QPushButton("Cerrar")

        botones = QHBoxLayout()

        botones.addWidget(self.btn_exportar)
        botones.addWidget(self.btn_importar)
        botones.addWidget(self.btn_cancelar)
        botones.addWidget(self.btn_cerrar)

        layout.addLayout(botones)

        self.btn_exportar.clicked.connect(self.exportar)
        self.btn_importar.clicked.connect(self.importar)
        self.btn_cancelar.clicked.connect(self.cancelar_operacion)
        self.btn_cerrar.clicked.connect(self.accept)

        # Obtenemos la ruta padre para añadirla a "copia_seguridad", que es
        #   donde tenemos el archivo de la exportación.
        if getattr(sys, "frozen", False):
            ruta_app = Path(sys.executable).parent
        else:
            ruta_app = Path(__file__).resolve().parent

        self.ruta_destino = ruta_app / "copia_seguridad"
        self.ruta_destino.mkdir(parents=True, exist_ok=True)

        self.habilitar_botones(True)
        self.comprobar_datos()

    def exportar(self):       
        archivo, _ = QFileDialog.getSaveFileName(self, "Exportar Biblioteca", str(self.ruta_destino), "Biblioteca (*.fbk)")

        if not archivo:
            return
        
        self.habilitar_botones(False)        
        self.exportarSolicitado.emit(archivo)

    def importar(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Importar Biblioteca", str(self.ruta_destino), "Biblioteca (*.fbk)")

        if not archivo:
            return
        
        self.habilitar_botones(False)        
        self.importarSolicitado.emit(archivo)

    def actualizar_metadatos(self, valor):
        self.barra_metadatos.setValue(valor)

    def actualizar_miniaturas(self, valor):
        self.barra_miniaturas.setValue(valor)

    def actualizar_fotos(self, valor):
        self.barra_fotos.setValue(valor)

    def actualizar_comprension(self, valor):
        self.barra_compresion.setValue(valor)

    def actualizar_descomprension(self, valor):
        self.barra_compresion.setValue(valor)

    def actualizar_tiempo(self, texto):
        self.lbl_tiempo.setText(f"Tiempo restante: {texto}")

    def actualizar_archivo(self, texto):
        self.lbl_archivo.setText(texto)

    def actualizar_estado(self, texto):
        self.lbl_estado.setText(texto)

    def cancelar_operacion(self):
        self.cancelarSolicitado.emit()

    def habilitar_botones(self, valor):
        self.btn_exportar.setEnabled(valor)
        self.btn_importar.setEnabled(valor)
        self.btn_cerrar.setEnabled(valor)
        self.btn_cancelar.setEnabled(not valor)

    def comprobar_datos(self):
        data = cargar_json_unico(ruta_json_unico())
        clasificados = data["stats"]["total_clasificados"]
        self.btn_exportar.setEnabled(clasificados > 0)
