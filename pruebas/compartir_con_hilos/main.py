'''
Ventana PyQt lista para integrar y compartir varios archivos.
Incluye:
    Selección múltiple de archivos.
    Envío por email con barra de progreso.
    Guardado automático de configuración.
    Compartir por enlace (con QR)
'''

import sys
import os
from config_correo import ConfigCorreo
from email_worker import EmailWorker
from compartidor import Compartidor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QMessageBox, QLabel, QDialog, QLineEdit, QFormLayout,
    QProgressBar
)
from PyQt5.QtGui import QPixmap

contraseña = "enyn ytju bege yrce"

class VentanaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compartir archivos")
        self.resize(400, 300)

        self.config = ConfigCorreo()

        layout = QVBoxLayout(self)

        self.botonSeleccionar = QPushButton("Seleccionar archivos")
        self.botonEmail = QPushButton("Enviar por email")
        self.botonEnlace = QPushButton("Compartir por enlace")
        self.progreso_archivo = QProgressBar()
        self.progreso_global = QProgressBar()

        self.botonEmail.setEnabled(False)
        self.botonEnlace.setEnabled(False)
        self.progreso_archivo.setValue(0)
        self.progreso_global.setValue(0)

        layout.addWidget(self.botonSeleccionar)
        layout.addWidget(self.botonEmail)
        layout.addWidget(self.botonEnlace)

        layout.addWidget(QLabel("Progreso del archivo actual:"))
        layout.addWidget(self.progreso_archivo)

        layout.addWidget(QLabel("Progreso total:"))
        layout.addWidget(self.progreso_global)

        self.botonSeleccionar.clicked.connect(self.seleccionar_archivos)
        self.botonEmail.clicked.connect(self.enviar_email)
        self.botonEnlace.clicked.connect(self.compartir_enlace)

        self.archivos = []

    def seleccionar_archivos(self):
        rutas, _ = QFileDialog.getOpenFileNames(self, "Seleccionar archivos")
        if rutas:
            self.archivos = rutas
            self.botonEmail.setEnabled(True)
            self.botonEnlace.setEnabled(True)

    def enviar_email(self):
        correo, password = self.config.cargar()

        # Ventana para pedir datos del correo
        dlg = QDialog(self)
        dlg.setWindowTitle("Enviar email")
        form = QFormLayout(dlg)

        txtDestino = QLineEdit()
        txtOrigen = QLineEdit(correo)
        txtPass = QLineEdit(password)
        txtPass.setEchoMode(QLineEdit.Password)

        form.addRow("Correo destino:", txtDestino)
        form.addRow("Tu correo:", txtOrigen)
        form.addRow("Contraseña:", txtPass) # enyn ytju bege yrce

        btnEnviar = QPushButton("Enviar")
        form.addWidget(btnEnviar)

        def procesar():
            self.config.guardar(txtOrigen.text(), txtPass.text())

            self.worker = EmailWorker(
                archivos=self.archivos,
                destino=txtDestino.text(),
                origen=txtOrigen.text(),
                password=txtPass.text()
            )

            self.worker.progreso_archivo.connect(self.progreso_archivo.setValue)
            self.worker.progreso_global.connect(self.progreso_global.setValue)
            self.worker.terminado.connect(self.fin_envio)
            self.worker.start()
            dlg.accept()

        btnEnviar.clicked.connect(procesar)
        dlg.exec_()

    def fin_envio(self, ok, mensaje):
        # Detener el hilo de forma segura
        self.worker.quit()
        self.worker.wait()

        if ok:
            QMessageBox.information(self, "Email", mensaje)
        else:
            print(mensaje)
            QMessageBox.critical(self, "Error", mensaje)

        # Resetear barras
        self.progreso_archivo.setValue(0)
        self.progreso_global.setValue(0)

    def compartir_enlace(self):
        if not self.archivos:
            return
        
        url = Compartidor.compartir_varios_archivos(self.archivos, minutos=3)

        dlg = QDialog(self)
        dlg.setWindowTitle("Compartir archivos")
        layout = QVBoxLayout(dlg)

        pixmap = Compartidor.generar_qr(url)
        lbl = QLabel(f"Escanea este QR o abre:\n{url}")
        qr = QLabel()
        qr.setPixmap(pixmap)

        layout.addWidget(lbl)
        layout.addWidget(qr)

        dlg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec_())
