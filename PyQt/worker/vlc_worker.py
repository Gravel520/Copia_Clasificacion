'''
Script en Python.
'''

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot

class VLCWorker(QThread):
    video_loaded = pyqtSignal()
    stopped = pyqtSignal()

    def __init__(self, instance, mediaplayer, parent=None):
        super().__init__(parent)
        self.instance = instance
        self.mediaplayer = mediaplayer
        self.file_to_load = None
        self.command = None

        # Flag de control
        self.detener = False
        self._running = True

    def run(self):
        while self._running and not self.detener:

            # Cargar video
            if self.command == "load" and self.file_to_load:
                try:
                    media = self.instance.media_new(self.file_to_load)
                    self.mediaplayer.set_media(media)
                    self.mediaplayer.play()
                    self.video_loaded.emit()
                except Exception as e:
                    print("Error al cargar video:", e)

                self.command = None
                self.file_to_load = None

            # Detener vídeo
            elif self.command == "stop":
                try:
                    self.mediaplayer.stop()
                except:
                    pass

                self.stopped.emit()
                self.command = None

            self.msleep(10)

        # Limpieza final del hilo
        try:
            self.mediaplayer.stop()
            self.mediaplayer.set_media(None)
        except:
            pass

    def stop_thread(self):
        # Detener el hilo de forma segura.
        self._running = False
        self.detener = True
        self.command = None
        
        try:
            self.mediaplayer.stop()
            self.mediaplayer.set_media(None)
        except:
            pass
        