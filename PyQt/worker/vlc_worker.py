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
        self._running = True

    def run(self):
        while self._running:
            if self.command == "load" and self.file_to_load:
                media = self.instance.media_new(self.file_to_load)
                self.mediaplayer.set_media(media)
                self.mediaplayer.play()
                self.video_loaded.emit()
                self.command = None
                self.file_to_load = None

            elif self.command == "stop":
                self.mediaplayer.stop()
                self.stopped.emit()
                self.command = None

            self.msleep(10)

    def stop_thread(self):
        self._running = False
        self.command = None
        