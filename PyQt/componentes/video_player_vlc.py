'''
Script en Python.
El parámetro 'solo_video', lo utilizamos para elegir los archivos que vamos
    a visualizar, todos o solo los videos. El parámetro viene desde la clase
    'VentanaCarpetasVideo' donde se cuentas los archivos de video que hay en
    cada carpeta y se pueden visualizar.

'''

import sys
import vlc
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QSlider, QLabel, QFrame, QGraphicsView, QGraphicsScene,
)
from PyQt5.QtCore import Qt, QTime, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QTransform, QPainter
from PIL import Image
from config_paths import extensiones_validas, get_assets
from worker.vlc_worker import VLCWorker


class VideoPlayer(QWidget):
    def __init__(self, ruta_visualizado, archivo, datos, solo_videos=None):
        super().__init__()
        self.ruta_carpeta = ruta_visualizado

        # Lista de archivos válidos, si son solo videos o tambien imágenes.
        ext = extensiones_validas("video") if solo_videos else (
            extensiones_validas("video") + extensiones_validas("imagen")
        )

        self.lista_archivos = [
            f for f in os.listdir(self.ruta_carpeta)
            if f.lower().endswith(ext)
        ]

        self.indice = self.lista_archivos.index(os.path.basename(archivo))
        self.archivo_actual = os.path.join(self.ruta_carpeta, self.lista_archivos[self.indice])

        self.setWindowTitle(os.path.basename(archivo))
        self.resize(1000, 650)

        # Añadimos atributos para rotar la imagen.
        self.archivo_original = archivo
        self.pixmap_actual = None

        # Comprobamos si es imagen o video.
        self.es_imagen = archivo.lower().endswith(extensiones_validas("imagen"))
        self.es_video = archivo.lower().endswith(extensiones_validas("video"))
        if solo_videos: self.es_imagen = False

        # Estilo general oscuro
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #666;
                border: 1px solid #555;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QSlider::groove_horizontal {
                height: 6px;
                background: #444;
            }
            QSlider::handle:horizontal {
                background: #ddd;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)

        # Instancia VLC
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()
        self.archivo_pendiente = None

        # Widget central donde se mostrará el video
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_layout = QVBoxLayout(self.video_frame)
        self.video_layout.setContentsMargins(0, 0, 0, 0)

        # Asignar el handle ANTES de usar el hilo
        self._set_video_widget()

        # Instanciar hilo de VLC
        self.vlc_thread = VLCWorker(self.instance, self.mediaplayer, parent=self)
        self.vlc_thread.video_loaded.connect(self._on_video_loaded)
        self.vlc_thread.stopped.connect(self._on_vlc_stopped)
        self.vlc_thread.start()

        # --------------------------
        # BOTONES GRANDES CON ICONOS
        # --------------------------
        # Botones del video.
        self.play_btn = QPushButton()
        self.play_btn.setIcon(QIcon(f'{get_assets()}play.png'))
        self.play_btn.setToolTip("Reproducir / Pausa")
        self.play_btn.setIconSize(QSize(32, 32))
        self.play_btn.setFixedSize(50, 50)

        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(QIcon(f'{get_assets()}detener.png'))
        self.stop_btn.setToolTip("Detener")
        self.stop_btn.setIconSize(QSize(32, 32))
        self.stop_btn.setFixedSize(50, 50)

        self.play_btn.clicked.connect(self.play_pause)
        self.stop_btn.clicked.connect(self.stop)

        # Botones de la imagen.
        self.rotar_izq_btn = QPushButton()
        self.rotar_izq_btn.setIcon(QIcon(f'{get_assets()}girar_izquierda.png'))
        self.rotar_izq_btn.setToolTip("Girar Izquierda")
        self.rotar_izq_btn.setIconSize(QSize(32, 32))
        self.rotar_izq_btn.setFixedSize(50, 50)

        self.rotar_der_btn = QPushButton()
        self.rotar_der_btn.setIcon(QIcon(f'{get_assets()}girar_derecha.png'))
        self.rotar_der_btn.setToolTip("Girar Derecha")
        self.rotar_der_btn.setIconSize(QSize(32, 32))
        self.rotar_der_btn.setFixedSize(50, 50)

        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(QIcon(f'{get_assets()}anterior.png'))
        self.btn_prev.setToolTip("Imagen Anterior")
        self.btn_prev.setIconSize(QSize(32, 32))
        self.btn_prev.setFixedSize(32, 32)

        self.btn_next = QPushButton()
        self.btn_next.setIcon(QIcon(f'{get_assets()}siguiente.png'))
        self.btn_next.setToolTip("Imagen Siguiente")
        self.btn_next.setIconSize(QSize(32, 32))
        self.btn_next.setFixedSize(32, 32)

        self.rotar_izq_btn.clicked.connect(lambda: self.rotar_imagen(-90))
        self.rotar_der_btn.clicked.connect(lambda: self.rotar_imagen(90))
        self.btn_prev.clicked.connect(self.archivo_anterior)
        self.btn_next.clicked.connect(self.archivo_siguiente)

        # Datos del archivo.
        self.datos_lb = QLabel(datos)
        self.datos_lb.setStyleSheet("color: #bbb; font-size: 18px;")

        # Si solo hay un archivo, deshabilitamos los botones de
        #   avance y retroceso de archivo.
        habilitar = len(self.lista_archivos) > 1
        self.btn_next.setEnabled(habilitar)
        self.btn_prev.setEnabled(habilitar)        

        # ------------------
        # SLIDER DE PROGRESO
        # ------------------
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setToolTip("Tiempo de Video")
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderMoved.connect(self.set_position)

        # Etiqueta de tiempo
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("font-size: 13px; color: #ccc;")        

        # -----------------
        # SLIDER DE VOLUMEN
        # -----------------
        self.volumen_slider = QSlider(Qt.Horizontal)
        self.volumen_slider.setToolTip("Volumen")
        self.volumen_slider.setRange(0, 100)
        self.volumen_slider.setValue(50)
        self.volumen_slider.setFixedWidth(120)
        self.volumen_slider.sliderMoved.connect(self.set_volume)

        # Icono de volumen
        self.vol_icon = QLabel("🔊")
        self.vol_icon.setFont(QFont("Arial", 18))

        # -------------------
        # LAYOUT DE CONTROLES
        # -------------------
        control_layout = QHBoxLayout()
        control_layout.setSpacing(15)
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addSpacing(20)
        control_layout.addWidget(self.datos_lb)
        control_layout.addStretch()
        control_layout.addWidget(self.time_label)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.vol_icon)
        control_layout.addWidget(self.volumen_slider)
        control_layout.addWidget(self.rotar_izq_btn)
        control_layout.addWidget(self.rotar_der_btn)

        # Layout superior. Posterior y anterior
        movie_layout = QHBoxLayout()
        movie_layout.addStretch()
        movie_layout.addWidget(self.btn_prev)
        movie_layout.addWidget(self.btn_next)

        # Layout inferior
        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.position_slider)
        bottom_layout.addLayout(control_layout)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addLayout(movie_layout)
        main_layout.addWidget(self.video_frame)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        # Comprobar si es imagen.
        if self.es_imagen:
            self.update_controls(True) # Habilitar controles de imagen.
            self.mostrar_imagen(archivo)

        else:
            self.update_controls(False) # Habilitar controles de video.
            # Timer para actualizar la UI
            self.timer = QTimer(self)
            self.timer.setInterval(500)
            self.timer.timeout.connect(self.update_ui)
            self.timer.start()

            self.open_file(archivo)

    # -----------------------------------
    # MOSTRAR LA IMAGEN EN EL REPRODUCTOR
    # -----------------------------------
    def mostrar_imagen(self, archivo):
        self.image_viewer = ImageViewer()

        img = Image.open(archivo)
        exif = img.getexif()
        orientacion = exif.get(274, 1)

        pix = QPixmap(archivo)
        transform = QTransform()

        if orientacion == 3:
            transform.rotate(180)
        elif orientacion == 6:
            transform.rotate(90)
        elif orientacion == 8:
            transform.rotate(270)

        pix = pix.transformed(transform)
        self.pixmap_actual = pix # Guardamos el pixmap original

        # Limpiar contenido anterior
        for i in reversed(range(self.video_layout.count())):
            widget = self.video_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.video_layout.addWidget(self.image_viewer)
        self.image_viewer.set_image(pix)

    def mostrar_imagen_pantalla(self, pix):
            self.image_label.setPixmap(
                pix.scaled(
                    self.video_frame.size(), 
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                    )
            )
            
    # ---------------------------------
    # FUNCIONES DEL VISUALIZADOR IMAGEN
    # ---------------------------------
    def rotar_imagen(self, grados):
        if not self.es_imagen or self.pixmap_actual is None:
            return
        
        transform = QTransform().rotate(grados)
        self.pixmap_actual = self.pixmap_actual.transformed(transform, Qt.SmoothTransformation)

        # Mostrar en pantalla
        self.image_viewer.set_image(self.pixmap_actual)

        # Guardar en el archivo original
        self.pixmap_actual.save(self.archivo_original)

    def archivo_anterior(self):
        self.indice = (self.indice - 1) % len(self.lista_archivos)
        self.cargar_archivo_actual()

    def archivo_siguiente(self):
        self.indice = (self.indice + 1) % len(self.lista_archivos)
        self.cargar_archivo_actual()

    def cargar_archivo_actual(self):
        self.archivo_actual = os.path.join(self.ruta_carpeta, self.lista_archivos[self.indice])

        # Actualizar título
        self.setWindowTitle(self.lista_archivos[self.indice])

        # Limpiar frame
        for i in reversed(range(self.video_layout.count())):
            widget = self.video_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Detectar tipo
        self.es_imagen = self.archivo_actual.lower().endswith(extensiones_validas("imagen"))
        self.es_video = self.archivo_actual.lower().endswith(extensiones_validas("video"))

        if self.es_imagen:
            self.mediaplayer.stop()
            self.update_controls(True)
            self.mostrar_imagen(self.archivo_actual)
            return

        # Si es video esperar a que VLC pare
        self.update_controls(False)
        self.archivo_pendiente = self.archivo_actual
        self.vlc_thread.command = "stop"

    # -----------------------------
    # FUNCIONES DEL REPRODUCTOR VLC
    # -----------------------------
    def open_file(self, file_name):
        self.vlc_thread.file_to_load = file_name
        self.vlc_thread.command = "load"

    def _set_video_widget(self):
        # Asignar el handle de la ventana según plataforma
        if sys.platform.startswith("linux"):
            self.mediaplayer.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":
            self.mediaplayer.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":
            # macOS requiere el NSView/NSWindow; PyQt5 devuelve un sip.usaable handle en algunos casos
            self.mediaplayer.set_nsobject(int(self.video_frame.winId()))

    def play_pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.play_btn.setIcon(QIcon(f'{get_assets()}play.png'))
        else:
            self.mediaplayer.play()
            self.play_btn.setIcon(QIcon(f'{get_assets()}pausa.png'))

    def stop(self):
        self.vlc_thread.command = "stop"

    def set_volume(self, value):
        self.mediaplayer.audio_set_volume(value)

    def set_position(self, pos):
        self.mediaplayer.set_position(pos / 1000.0)

    def _on_video_loaded(self):
        self.play_btn.setIcon(QIcon(f'{get_assets()}pausa.png'))

    def _on_vlc_stopped(self):
        if self.archivo_pendiente:
            archivo = self.archivo_pendiente
            self.archivo_pendiente = None
            self.open_file(archivo)

    # ----------------------
    # ACTUALIZACION DE LA UI
    # ----------------------
    def update_ui(self):
        if not self.mediaplayer:
            return
        
        # Actualizar slider
        pos = self.mediaplayer.get_position()
        if pos > 0:
            self.position_slider.setValue(int(pos * 1000))

        # Actualizar tiempo
        length = self.mediaplayer.get_length()
        time = self.mediaplayer.get_time()

        def fmt(ms):
            t = QTime(0, 0, 0).addMSecs(ms)
            return t.toString("hh:mm:ss") if length >= 3600_000 else t.toString("mm:ss")
        
        if length > 0:
            self.time_label.setText(f"{fmt(time)} / {fmt(length)}")

        if fmt(length) == fmt(time):
            self.stop()

    # -----------------------------
    # ACTUALIZAR BARRA DE CONTROLES
    # -----------------------------
    def update_controls(self, valor):
        self.play_btn.setEnabled(not valor)
        self.stop_btn.setEnabled(not valor)
        self.rotar_izq_btn.setEnabled(valor)
        self.rotar_der_btn.setEnabled(valor)
        self.position_slider.setEnabled(not valor)
        self.volumen_slider.setEnabled(not valor)

    def closeEvent(self, a0):
        try:
            if self.mediaplayer:
                self.mediaplayer.stop()
        except:
            pass
        
        a0.accept()

class ImageViewer(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap_item = None

    def set_image(self, pixmap):
        self.scene.clear()
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 0.8

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        self.scale(zoom_factor, zoom_factor)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VideoPlayer()
    w.show()
    sys.exit(app.exec_())
