'''
El envío por email debe hacerse en un QThread, porque si no la interfaz
se congela. Además, podemos emitir señales para actualizar una barra
de progreso.
'''

import smtplib
import mimetypes
import os
import time
from PyQt5.QtCore import QThread, pyqtSignal
from email.message import EmailMessage

CONTRASEÑA = "enyn ytju bege yrce"

class EmailWorker(QThread):
    progreso_archivo = pyqtSignal(int) # Progreso del archivo actual
    progreso_global = pyqtSignal(int) # Progreso total
    terminado = pyqtSignal(bool, str)

    def __init__(self, archivos, destino, origen, password):
        super().__init__()
        self.archivos = archivos
        self.destino = destino
        self.origen = origen
        self.password = password

    def run(self):
        try:
            total_archivos = len(self.archivos)
            enviados = 0
            porcentaje_global = 0

            # Emitimos progreso inicial
            self.progreso_archivo.emit(0)
            self.progreso_global.emit(0)

            for archivo in self.archivos:
                # --- PROGRESO DEL ARCHIVO ---
                tamaño = os.path.getsize(archivo)
                enviado = 0

                msg = EmailMessage()
                msg["Subject"] = "Archivos compartidos"
                msg["From"] = self.origen
                msg["To"] = self.destino
                msg.set_content("Te envío estos archivos.")

                mime, _ = mimetypes.guess_type(archivo)
                maintype, subtype = mime.split("/")

                contenido = b""

                # Leer en bloques para progreso fino
                with open(archivo, "rb") as f:
                    chunk = f.read(65536) # 64 KB
                    while chunk:
                        contenido += chunk
                        enviado += len(chunk)

                        # Progreso fino por bytes
                        porcentaje_archivo = int((enviado / tamaño) * 100)
                        self.progreso_archivo.emit(porcentaje_archivo)

                        time.sleep(0.01) # Hace visible la evolución.

                        chunk = f.read(65536)

                    msg.add_attachment(
                        contenido,
                        maintype=maintype,
                        subtype=subtype,
                        filename=os.path.basename(archivo)
                    )

                # --- ENVÍO DEL EMAIL ---
                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                    smtp.login(self.origen, self.password)
                    smtp.send_message(msg)

                # --- PROGRESO GLOBAL ---
                enviados += 1
                porcentaje_global = int((enviados / total_archivos) * 100)
                self.progreso_global.emit(porcentaje_global)

            self.terminado.emit(True, "Envio completado")

        except Exception as e:
            self.terminado.emit(False, f"Worker: {str(e)}")
            