'''
Instalar VLC (la forma más simple)
Instala VLC desde la web oficial (versión de 64 bits si tu Python es 64 bits):
https://www.videolan.org/vlc/

Asegúrate de que VLC esté instalado en:

Código
C:\Program Files\VideoLAN\VLC\
Reinicia tu script.
'''

import sys
import vlc
from PyQt5 import QtWidgets, QtCore, QtGui

class VLCPlayer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC + PyQt5")
        self.resize(900, 600)

        # Instancia VLC
        self.instance = vlc.Instance()
        self.mediaplayer = self.instance.media_player_new()

        # Widget central donde se mostrará el video
        self.video_frame = QtWidgets.QFrame()
        self.setCentralWidget(self.video_frame)

        # Controles básicos
        open_btn = QtWidgets.QPushButton("Abrir")
        play_btn = QtWidgets.QPushButton("Reproducir/Pausar")
        stop_btn = QtWidgets.QPushButton("Detener")

        open_btn.clicked.connect(self.open_file)
        play_btn.clicked.connect(self.play_pause)
        stop_btn.clicked.connect(self.stop)

        # Layout inferior
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(open_btn)
        hbox.addWidget(play_btn)
        hbox.addWidget(stop_btn)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.video_frame)
        vbox.addLayout(hbox)

        container = QtWidgets.QWidget()
        container.setLayout(vbox)
        self.setCentralWidget(container)

        # Timer para actualizar estado (opcional)
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_ui)
        self.timer.start()

    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Seleccionar video", "", "Videos (*.mp4 *.mkv *.avi *.mov)")
        if path:
            media = self.instance.media_new(path)
            self.mediaplayer.set_media(media)
            self._set_video_widget()
            self.mediaplayer.play()

    def _set_video_widget(self):
        # Asignar el handle de la ventana según plataforma
        if sys.platform.startswith("linux"):
            self.mediaplayer.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32":
            self.mediaplayer.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin":
            # macOS requiere el NSView/NSWindow; PyQt5 devuelve un sip.usaable handle en algunos casos
            self.mediaplayer.set_nsobject(int(self.video_frame.winId()))
        else:
            self.mediaplayer.set_xwindow(self.video_frame.winId())

    def play_pause(self):
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
        else:
            self.mediaplayer.play()

    def stop(self):
        self.mediaplayer.stop()

    def update_ui(self):
        # Aquí puedes actualizar sliders, tiempo, etc.
        pass

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    player = VLCPlayer()
    player.show()
    sys.exit(app.exec_())
