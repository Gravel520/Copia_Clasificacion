'''

'''

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QFileDialog, QSlider, QLabel, QSizePolicy
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QTime, QTimer

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reproductos de Video - PyQt5")
        self.resize(900, 600)

        # Player y widget de video
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.video_widget = QVideoWidget()

        # Botones
        self.open_btn = QPushButton("Abrir")
        self.play_btn = QPushButton("Reproducir")
        self.stop_btn = QPushButton("Detener")

        self.open_btn.clicked.connect(self.open_file)
        self.play_btn.clicked.connect(self.play_pause)
        self.stop_btn.clicked.connect(self.stop)

        # Slider de progreso
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)

        # Slider de volumen
        self.volumen_slider = QSlider(Qt.Horizontal)
        self.volumen_slider.setRange(0, 100)
        self.volumen_slider.setValue(50)
        self.volumen_slider.sliderMoved.connect(self.player.setVolume)

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
        main_layout.addWidget(self.video_widget)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        # Conectar player con widget de video
        self.player.setVideoOutput(self.video_widget)

        # Señales del player
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.stateChanged.connect(self.state_changed)

        # Temporizador para actualizar tiempo (opcional)
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_time)
        self.timer.start()

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar video", "", "Videos (*.mp4 *.avi *.mkv *.mov)")
        if file_name:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_name)))
            
            print("mediaStatus: ", self.player.mediaStatus())
            print("error: ", self.player.error())
            print("errorString: ", self.player.errorString())

            self.player.play()
            self.play_btn.setText("Pausar")

    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("Reproducir")
        else:
            self.player.play()
            self.play_btn.setText("Pausar")

    def stop(self):
        self.player.stop()
        self.play_btn.setText("Reproducir")

    def position_changed(self, position):
        self.position_slider.setValue(position)

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time()

    def set_position(self, pos):
        self.player.setPosition(pos)

    def state_changed(self, state):
        if state == QMediaPlayer.StoppedState:
            self.play_btn.setText("Reproducir")

    def update_time(self):
        pos = self.player.position()
        dur = self.player.duration()
        def fmt(ms):
            t = QTime(0, 0, 0).addMSecs(ms)
            if dur >= 3600_000:
                return t.toString("hh:mm:ss")
            return t.toString("mm:ss")
        self.time_label.setText(f"{fmt(pos)} / {fmt(dur)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = VideoPlayer()
    w.show()
    sys.exit(app.exec_())
