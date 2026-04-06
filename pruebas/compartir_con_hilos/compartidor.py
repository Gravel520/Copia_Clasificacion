'''
Esta clase encapsula toda la lógica para enviar archivos por email o
por servidor local
'''

import smtplib
import mimetypes
import http.server
import socketserver
import threading
import socket
import os
import qrcode
import time
import io
from PIL import Image
from email.message import EmailMessage
from io import BytesIO
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel

class Compartidor:
    @staticmethod
    def enviar_email(archivo, destino, correo_origen, password,
                     asunto="Archivo compartido", cuerpo="Te envio este archivo."):
        
        msg = EmailMessage()
        msg["Subject"] = asunto
        msg["From"] = correo_origen
        msg["To"] = destino
        msg.set_content(cuerpo)

        mime_type, _ = mimetypes.guess_type(archivo)
        maintype, subtype = mime_type.split("/")

        with open(archivo, "rb") as f:
            msg.add_attachment(
                f.read(),
                maintype=maintype,
                subtype=subtype,
                filename=os.path.basename(archivo)
                )
            
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(correo_origen, password)
            smtp.send_message(msg)

    @staticmethod
    def obtener_ip_local():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    
    @staticmethod
    def compartir_por_servidor(ruta_archivo, puerto=8000):
        directorio = os.path.dirname(ruta_archivo)
        nombre = os.path.basename(ruta_archivo)

        os.chdir(directorio)

        class FileHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/" + nombre:
                    self.send_response(200)
                    mime, _ = mimetypes.guess_type(nombre)
                    self.send_header("Content-type", mime or "application/octet-stream")
                    self.end_headers()
                    with open(ruta_archivo, "rb") as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404, "Archio no encontrado")

        def servidor():
            with socketserver.TCPServer(("", puerto), FileHandler) as httpd:
                print(f"Servidor activo en http://0.0.0.0:{puerto}/{nombre}")
                httpd.serve_forever()

        hilo = threading.Thread(target=servidor, daemon=True)
        hilo.start()

        ip = Compartidor.obtener_ip_local()
        return f"http://{ip}:{puerto}/{nombre}"
    
    @staticmethod
    def generar_qr(url):
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap
    
    # --------------------------
    # SERVIDOR MULTI-ARCHIVO
    # --------------------------
    @staticmethod
    def compartir_varios_archivos(archivos, puerto=8000, minutos=5):
        class Handler(MultiFileHandler):
            pass

        Handler.archivos = archivos

        httpd = socketserver.TCPServer(("", puerto), Handler)

        def servidor():
            print(f"Servidor activo en http://0.0.0.0:{puerto}/ (se apagará en {minutos} minutos.)")
            httpd.serve_forever()

        hilo = threading.Thread(target=servidor, daemon=True)
        hilo.start()

        # Autodesconexión
        def apagar():
            print("Apagando servidor de compartición...")
            httpd.shutdown()
            httpd.server_close()

        timer = threading.Timer(minutos * 60, apagar)
        timer.daemon = True
        timer.start()

        ip = Compartidor.obtener_ip_local()
        return f"http://{ip}:{puerto}/"
    
class MultiFileHandler(http.server.SimpleHTTPRequestHandler):
    archivos = [] # Se rellenará desde fuera

    def do_GET(self):

        # ---------------------------
        # MINIATURAS /thumb/<archivo>
        # ---------------------------
        if self.path.startswith("/thumb/"):
            nombre = self.path.replace("/thumb/", "")
            for archivo in self.archivos:
                if os.path.basename(archivo) == nombre:
                    try:
                        img = Image.open(archivo)
                        img.thumbnail((200, 200))

                        buffer = io.BytesIO()
                        img.save(buffer, format="JPEG", quality=70)
                        buffer.seek(0)

                        self.send_response(200)
                        self.send_header("Content-type", "image/jpeg")
                        self.end_headers()
                        self.wfile.write(buffer.getvalue())
                        return
                    except:
                        break

            self.send_error(404, "Miniatura no disponible")
            return

        # ---------------------------
        # PÁGINA PRINCIPAL
        # ---------------------------
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = """
            <!doctype html>
            <html lang="es">
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Archivos compartidos</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <style>
                    body { padding: 20px; }
                    .thumb {
                        width: 100%;
                        height: 150px;
                        object-fit: cover;
                        border-radius: 6px;
                        background: #eee;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2 class="mb-4">Archivos disponibles</h2>
                    <div class="row g-3">
            """

            for archivo in self.archivos:
                nombre = os.path.basename(archivo)
                mime, _ = mimetypes.guess_type(nombre)
                es_imagen = mime and mime.startswith("image/")

                html += '<div class="col-6 col-md-4 col-lg-3">'
                html += '<div class="card h-100 p-2">'

                if es_imagen:
                    html += f'<a href="/file/{nombre}">'
                    html += f'<img src="/thumb/{nombre}" class="thumb" alt="{nombre}">'
                    html += '</a>'
                else:
                    html += '<div class="thumb d-flex align-items-center justify-content-center">'
                    html += '<span class="text-muted">Archivo</span>'
                    html += '</div>'

                html += f'<div class="mt-2 text-truncate">{nombre}</div>'
                html += f'<a href="/file/{nombre}" class="btn btn-primary btn-sm mt-2">Descargar</a>'
                html += '</div></div>'

            html += """
                    </div>
                    <p class="mt-4 text-muted">Servidor local. Este enlace se apagará automáticamente.</p>
                </div>
            </body>
            </html>
            """

            self.wfile.write(html.encode("utf-8"))
            return
        
        # ---------------------------
        # DESCARGA DEL ARCHIVO
        # ---------------------------
        if self.path.startswith("/file/"):
            nombre = self.path.replace("/file/", "")
            for archivo in self.archivos:
                if os.path.basename(archivo) == nombre:
                    self.send_response(200)
                    mime, _ = mimetypes.guess_type(nombre)
                    self.send_header("Content-type", mime or "application/octet-stream")
                    self.end_headers()
                    with open(archivo, "rb") as f:
                        self.wfile.write(f.read())
                    return
            self.send_error(404, "Archivo no encontrado")
            return
        
        self.send_error(404, "Ruta no válida.")
