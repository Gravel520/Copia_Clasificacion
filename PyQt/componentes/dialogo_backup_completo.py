'''
Script en Python.
'''

from PyQt5.QtWidgets import (QDialog, QLabel, QPushButton, QFileDialog,
                             QVBoxLayout, QHBoxLayout, QProgressBar,
                             QMessageBox)

from PyQt5.QtCore import pyqtSignal


class DialogoTransferencia(QDialog):
    exportarSolicitado = pyqtSignal(str)
    importarSolicitado = pyqtSignal(str)
    cancelarSolicitado = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle("Transferencia Biblioteca")

        self.resize(450, 180)

        layout = QVBoxLayout(self)

        self.lbl_estado = QLabel("Esperando...")
        self.lbl_estado.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                color: #2c3e50;
                font-weight: bold;
            }
        """)
        self.barra = QProgressBar()

        self.btn_exportar = QPushButton("Exportar")
        self.btn_importar = QPushButton("Importar")
        self.btn_cancelar = QPushButton("Cancelar")

        layout.addWidget(self.lbl_estado)
        layout.addWidget(self.barra)

        botones = QHBoxLayout()

        botones.addWidget(self.btn_exportar)
        botones.addWidget(self.btn_importar)
        botones.addWidget(self.btn_cancelar)

        layout.addLayout(botones)

        self.btn_exportar.clicked.connect(self.exportar)
        self.btn_importar.clicked.connect(self.importar)
        self.btn_cancelar.clicked.connect(self.cancelar_operacion)

    def exportar(self):
        self.btn_exportar.setEnabled(False)
        self.btn_importar.setEnabled(False)
        
        archivo, _ = QFileDialog.getSaveFileName(self, "Exportar Biblioteca", "", "Biblioteca (*.fbk)")

        if not archivo:
            return
        
        self.exportarSolicitado.emit(archivo)

    def importar(self):
        self.btn_importar.setEnabled(False)
        self.btn_exportar.setEnabled(False)

        archivo, _ = QFileDialog.getOpenFileName(self, "Importar Biblioteca", "", "Biblioteca (*.fbk)")

        if not archivo:
            return
        
        self.importarSolicitado.emit(archivo)

    def actualizar_progreso(self, valor):
        self.barra.setValue(valor)

    def actualizar_estado(self, texto):
        self.lbl_estado.setText(texto)

    def operacion_finalizada(self, ok, mensaje):
        if ok:
            QMessageBox.information(self, "Biblioteca", "Operación completada.")
            self.btn_exportar.setEnabled(True)
            self.btn_importar.setEnabled(True)

        else:
            QMessageBox.critical(self, "Error", mensaje)

    def cancelar_operacion(self):
        self.cancelarSolicitado.emit()
