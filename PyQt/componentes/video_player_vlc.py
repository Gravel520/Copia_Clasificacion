'''

'''

import sys
import vlc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QSlider, QLabel, QFrame
)
from PyQt5.QtCore import Qt, QTime, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QTransform
from config_paths import extensiones_validas

assets = 'PyQt/assets/'

class VideoPlayer(QWidget):
    def __init__(self, archivo, datos):
        super().__init__()
        nombre_archivo = archivo.split("\\")[-1]
        self.setWindowTitle(nombre_archivo)
        self.resize(1000, 650)

        # Añadimos atributos para rotar la imagen.
        self.archivo_original = archivo
        self.pixmap_actual = None

        # Comprobamos si es imagen o video.
        self.es_imagen = archivo.lower().endswith(extensiones_validas("imagen"))
        self.es_video = archivo.lower().endswith(extensiones_validas("video"))

        # Estilo general oscuro
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #333;
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

        # Widget central donde se mostrará el video
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")

        # --------------------------
        # BOTONES GRANDES CON ICONOS
        # --------------------------
        # Botones del video.
        self.play_btn = QPushButton()
        self.play_btn.setIcon(QIcon(f'{assets}play.png'))
        self.play_btn.setToolTip("Reproducir / Pausa")
        self.play_btn.setIconSize(QSize(32, 32))
        self.play_btn.setFixedSize(50, 50)

        self.stop_btn = QPushButton()
        self.stop_btn.setIcon(QIcon(f'{assets}detener.png'))
        self.stop_btn.setToolTip("Detener")
        self.stop_btn.setIconSize(QSize(32, 32))
        self.stop_btn.setFixedSize(50, 50)

        self.play_btn.clicked.connect(self.play_pause)
        self.stop_btn.clicked.connect(self.stop)

        # Botones de la imagen.
        self.rotar_izq_btn = QPushButton()
        self.rotar_izq_btn.setIcon(QIcon(f'{assets}girar_izquierda.png'))
        self.rotar_izq_btn.setToolTip("Girar Izquierda")
        self.rotar_izq_btn.setIconSize(QSize(32, 32))
        self.rotar_izq_btn.setFixedSize(50, 50)

        self.rotar_der_btn = QPushButton()
        self.rotar_der_btn.setIcon(QIcon(f'{assets}girar_derecha.png'))
        self.rotar_der_btn.setToolTip("Girar Derecha")
        self.rotar_der_btn.setIconSize(QSize(32, 32))
        self.rotar_der_btn.setFixedSize(50, 50)

        self.rotar_izq_btn.clicked.connect(lambda: self.rotar_imagen(-90))
        self.rotar_der_btn.clicked.connect(lambda: self.rotar_imagen(90))

        # Datos del archivo.
        self.datos_lb = QLabel(datos)
        self.datos_lb.setStyleSheet("color: #bbb; font-size: 18px;")

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

        # Layout inferior
        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.position_slider)
        bottom_layout.addLayout(control_layout)

        # Layout principal
        main_layout = QVBoxLayout()
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
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)

        pix = QPixmap(archivo)
        self.pixmap_actual = pix # Guardamos el pixmap original

        # Mostramos en pantalla.
        self.mostrar_imagen_pantalla(pix)

        layout = QVBoxLayout(self.video_frame)
        layout.addWidget(self.image_label)

    def mostrar_imagen_pantalla(self, pix):
            self.image_label.setPixmap(pix.scaled(
            self.video_frame.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
    # ---------------------------------
    # FUNCIONES DEL VISUALIZADOR IMAGEN
    # ---------------------------------
    def rotar_imagen(self, grados):
        if not self.es_imagen or self.pixmap_actual is None:
            return
        
        transform = QTransform().rotate(grados)
        self.pixmap_actual = self.pixmap_actual.transformed(transform, Qt.SmoothTransformation)

        # Mostrar en pantalla
        self.mostrar_imagen_pantalla(self.pixmap_actual)

        # Guardar en el archivo original
        self.pixmap_actual.save(self.archivo_original)

    # -----------------------------
    # FUNCIONES DEL REPRODUCTOR VLC
    # -----------------------------
    def open_file(self, file_name):
        media = self.instance.media_new(file_name)
        self.mediaplayer.set_media(media)
        self._set_video_widget()
        self.mediaplayer.play()
        self.play_btn.setIcon(QIcon(f'{assets}pausa.png'))

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
            self.play_btn.setIcon(QIcon(f'{assets}play.png'))
        else:
            self.mediaplayer.play()
            self.play_btn.setIcon(QIcon(f'{assets}pausa.png'))

    def stop(self):
        self.mediaplayer.stop()
        self.play_btn.setIcon(QIcon(f'{assets}play.png'))

    def set_volume(self, value):
        self.mediaplayer.audio_set_volume(value)

    def set_position(self, pos):
        self.mediaplayer.set_position(pos / 1000.0)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VideoPlayer()
    w.show()
    sys.exit(app.exec_())
