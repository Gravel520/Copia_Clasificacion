'''

'''

from PyQt5.QtWidgets import QWidget, QStylePainter, QStyleOptionSlider
from PyQt5.QtCore import Qt, QRect, pyqtSignal


class QRangeSlider(QWidget):
    valueChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._min = 0
        self._max = 100
        self._start = 0
        self._end = 100
        self._bar_height = 6
        self._handle_radius = 8
        self._moving = None
        self.setMinimumHeight(30)        

    def setRange(self, min_val, max_val):
        self._min = min_val
        self._max = max_val
        self._start = min_val
        self._end = max_val
        self.update()

    def setValues(self, start, end):
        self._start = start
        self._end = end
        self.update()

    def paintEvent(self, event):
        painter = QStylePainter(self)
        opt = QStyleOptionSlider()
        opt.initFrom(self)

        # Track
        track_rect = QRect(10, self.height() // 2 - self._bar_height // 2,
                           self.width() - 20, self._bar_height)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.gray)
        painter.drawRect(track_rect)

        # Selected range
        start_x = 10 + (self._start - self._min) / (self._max - self._min) * (self.width() - 20)
        end_x = 10 + (self._end - self._min) / (self._max - self._min) * (self.width() - 20)

        selected_rect = QRect(int(start_x), track_rect.y(),
                              int(end_x - start_x), self._bar_height)
        painter.setBrush(Qt.blue)
        painter.drawRect(selected_rect)

        # Handles
        painter.setBrush(Qt.black)
        painter.drawEllipse(int(start_x) - self._handle_radius,
                            self.height() // 2 - self._handle_radius,
                            self._handle_radius * 2, self._handle_radius * 2)

        painter.drawEllipse(int(end_x) - self._handle_radius,
                            self.height() // 2 - self._handle_radius,
                            self._handle_radius * 2, self._handle_radius * 2)

    def mousePressEvent(self, event):
        x = event.x()
        start_x = 10 + (self._start - self._min) / (self._max - self._min) * (self.width() - 20)
        end_x = 10 + (self._end - self._min) / (self._max - self._min) * (self.width() - 20)

        # 1. Detectar si pulsamos cerca de los handles (prioridad)
        if abs(x - start_x) < 15:
            self._moving = "start"
        elif abs(x - end_x) < 15:
            self._moving = "end"

        # 2. Si pulsamos en la línea (fuera de los handles), movemos el más cercano.
        else:
            # Convertimos la posición X del clic a un valor del rango
            ratio = (x - 10) / (self.width() - 20)
            clicked_value = self._min + ratio * (self._max - self._min)
            clicked_value = max(self._min, min(self._max, int(clicked_value)))

            # Determinamos cuál de ls dos está más cerca del clic
            if abs(clicked_value - self._start) < abs(clicked_value - self._end):
                self._start = clicked_value
                self._moving = "start"
            else:
                self._end = clicked_value
                self._moving = "end"

            # Actualizamos y emitimos el cambio de inmediato
            self.valueChanged.emit(self._start, self._end)
            self.update()
            
    def mouseMoveEvent(self, event):
        if not self._moving:
            return

        x = event.x()
        ratio = (x - 10) / (self.width() - 20)
        value = self._min + ratio * (self._max - self._min)
        value = max(self._min, min(self._max, int(value)))

        if self._moving == "start":
            if value < self._end:
                self._start = value
        elif self._moving == "end":
            if value > self._start:
                self._end = value

        self.valueChanged.emit(self._start, self._end)
        self.update()

    def mouseReleaseEvent(self, event):
        self._moving = None
