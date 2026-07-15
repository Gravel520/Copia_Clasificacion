'''
Ventana PyQt lista para integrar y compartir varios archivos.
Incluye:
    Selección múltiple de archivos.
    Envío por email con barra de progreso.
    Guardado automático de configuración.
    Compartir por enlace (con QR)
'''

from PyQt5.QtWidgets import (
    QVBoxLayout, QPushButton,QMessageBox, QLabel, QDialog,
    QLineEdit, QFormLayout
    )
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QTimer

from .email_worker import EmailWorker
from .compartidor import Compartidor
from config_paths import get_enviando
from config_manager import settings
from utils.utils_correo import validar
from utils.thread_manager import thread_manager

class VentanaPrincipal(QDialog):
    def __init__(self, archivos):
        super().__init__()
        self.setWindowTitle("Compartir archivos")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        self.botonEmail = QPushButton("Enviar por email")
        self.botonEnlace = QPushButton("Compartir por enlace")

        # GIF animado
        self.lblGif = QLabel()
        self.lblGif.setFixedSize(375, 200)
        self.lblGif.setScaledContents(True)
        self.movie = QMovie(get_enviando())
        self.lblGif.setMovie(self.movie)
        self.lblGif.hide()

        # Estado
        self.lblEstado = QLabel("Listo para enviar")

        layout.addWidget(self.botonEmail)
        layout.addWidget(self.botonEnlace)
        layout.addWidget(self.lblGif)
        layout.addWidget(self.lblEstado)

        self.botonEmail.clicked.connect(self.enviar_email)
        self.botonEnlace.clicked.connect(self.compartir_enlace)

        self.archivos = archivos

    def enviar_email(self):
        # Ventana para pedir datos del correo
        dlg = QDialog(self)
        dlg.setWindowTitle("Enviar email")
        dlg.resize(300, 120)
        form = QFormLayout(dlg)

        lblDesde = QLabel(settings.value("Compartir/correo", ""))
        txtDestino = QLineEdit()

        form.addRow("Correo desde:", lblDesde)
        form.addRow("Correo destino:", txtDestino)

        btnEnviar = QPushButton("Enviar")
        form.addWidget(btnEnviar)

        def procesar():
            if validar(txtDestino):
                self.worker = EmailWorker(
                    archivos=self.archivos,
                    destino=txtDestino.text()
                )

                # Registrar el hilo en el gestor.
                thread_manager.add(self.worker)

                self.worker.archivo_enviado.connect(self.actualizar_estado)

                self.movie.start()
                self.lblGif.show()
                self.lblEstado.setText("Enviando archivos...")

                self.worker.terminado.connect(self.fin_envio)
                self.worker.start()
                dlg.accept()

            else:
                txtDestino.setStyleSheet("border: 2px solid red;")
                txtDestino.setFocus()

        btnEnviar.clicked.connect(procesar)
        dlg.exec_()

    def actualizar_estado(self, enviados, total):
        self.lblEstado.setText(f"Compartido {enviados} de {total} archivos")

    def fin_envio(self, ok, mensaje):
        # Detener el hilo de forma segura
        self.worker.quit()
        self.worker.wait()
        self.movie.stop()

        if ok:
            self.lblEstado.setText("Envio completado")
            QMessageBox.information(self, "Email", mensaje)
        else:
            self.lblEstado.setText("Error en el envío")
            QMessageBox.critical(self, "Error", mensaje)

    def compartir_enlace(self):
        if not self.archivos:
            return
        
        # Compartir por 3 minutos
        minutos = 3
        url, handle = Compartidor.compartir_varios_archivos(self.archivos, minutos=minutos)

        dlg = QDialog(self)
        dlg.setWindowTitle("Compartir archivos")
        layout = QVBoxLayout(dlg)

        pixmap = Compartidor.generar_qr(url)
        lbl = QLabel(f"Escanea este QR o abre:\n{url}")
        qr = QLabel()
        qr.setPixmap(pixmap)

        # Label del contador
        lbl_timer = QLabel()
        lbl_timer.setStyleSheet("font-size: 18px; font-weight: bold; color: blue;")

        layout.addWidget(lbl)
        layout.addWidget(qr)
        layout.addWidget(lbl_timer)

        # Guardar handle en el diálogo para poder apagar si el usuario cierra antes del timer.
        dlg.server_handle = handle

        # Tiempo restante en segundos.
        tiempo_restante = minutos * 60

        # Timer que actualiza cada segundo
        timer = QTimer(dlg)
        timer.setInterval(1000)

        def actualizar_contador():
            nonlocal tiempo_restante
            tiempo_restante -=1

            minutos_rest = tiempo_restante // 60
            segundos_rest = tiempo_restante % 60
            lbl_timer.setText(f"Tiempo restante: {minutos_rest:02d}:{segundos_rest:02d}")

            if tiempo_restante < 30:
                lbl_timer.setStyleSheet("font-size: 18px; font-weight: bold; color: red;")

            if tiempo_restante <= 0:
                timer.stop()
                try:
                    dlg.server_handle.shutdown()
                except Exception:
                    pass
                dlg.accept() # Cierra el diálogo automáticamente

        timer.timeout.connect(actualizar_contador)
        timer.start()

        def on_close():
            try:
                dlg.server_handle.shutdown()
            except Exception:
                pass

        dlg.finished.connect(lambda _: on_close())

        # Inicializar el contador visual
        actualizar_contador()

        dlg.exec_()
