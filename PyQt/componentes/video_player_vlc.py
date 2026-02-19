'''

'''

import sys
import vlc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QSlider, QLabel, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, QTime, QTimer

class VideoPlayer(QWidget):
    def __init__(self, archivo):
        super().__init__()
        self.setWindowTitle(archivo)
        self.resize(900, 600)

        # Instancia VLC
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()

        # Widget central donde se mostrará el video
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")

        # Botones
        self.open_btn = QPushButton("Abrir")
        self.play_btn = QPushButton("Reproducir/Pausar")
        self.stop_btn = QPushButton("Detener")

        #self.open_btn.clicked.connect(self.open_file)
        self.play_btn.clicked.connect(self.play_pause)
        self.stop_btn.clicked.connect(self.stop)

        # Slider de progreso
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderMoved.connect(self.set_position)

        # Slider de volumen
        self.volumen_slider = QSlider(Qt.Horizontal)
        self.volumen_slider.setRange(0, 100)
        self.volumen_slider.setValue(50)
        self.volumen_slider.sliderMoved.connect(self.set_volume)

        # Etiqueta de tiempo
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        # Layouts
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.open_btn)
        control_layout.addWidget(self.play_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(QLabel("Vol"))
        control_layout.addWidget(self.volumen_slider)

        bottom_layout = QVBoxLayout()
        bottom_layout.addWidget(self.position_slider)
        bottom_layout.addWidget(self.time_label)
        bottom_layout.addLayout(control_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_frame)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        # Timer para actualizar la UI
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

        self.open_file(archivo)

    # -----------------------------
    # Funciones del reproductos VLC
    # -----------------------------

    def open_file(self, file_name):
        '''
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar video", "", "Videos (*.mp4 *.avi *.mkv *.mov)"
            )
        if file_name:
        '''
        media = self.instance.media_new(file_name)
        self.mediaplayer.set_media(media)
        self._set_video_widget()
        self.mediaplayer.play()
        self.play_btn.setText("Pausar")

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
            self.play_btn.setText("Reproducir")
        else:
            self.mediaplayer.play()
            self.play_btn.setText("Pausar")

    def stop(self):
        self.mediaplayer.stop()
        self.play_btn.setText("Reproducir")

    def set_volume(self, value):
        self.mediaplayer.audio_set_volume(value)

    def set_position(self, pos):
        self.mediaplayer.set_position(pos / 1000.0)

    # -------------------
    # Actualización de UI
    # -------------------

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
