import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QCursor
from PySide6.QtCore import QTimer, QEvent
import qframelesswindow
import time

BOUNCE_FACTOR = 0.9
GRAVITY = 9.8
FRICTION = 1
THROW_FACTOR = 200
POP_FACTOR = 2
FPS = 60

# Class to handle the window stuff, such as the event handling and the settings stuff
class Window(qframelesswindow.AcrylicWindow):
    def __init__(self):        
        # basic setup stuff
        super().__init__()
        self.setWindowTitle("Wonky Window")
        self.setFixedSize(0, 0)
        self.setTitleBar(QWidget()) # oh my god thank you so much chatgpt this took like 2 hours to figure out
        self.toggleStayOnTop()

        # updating vars setup
        self.last_time: float = time.perf_counter()
        self.velX: float = 0
        self.velY: float = 0
        self.posX: float = 0
        self.posY: float = 0

        self.offsetX = 0
        self.offsetY = 0
        self.previousFramesX = [0, 0, 0, 0, 0, 0]
        self.previousFramesY = [0, 0, 0, 0, 0, 0]
        self.previousTimestamps = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.mouseDown: bool = False
        
        self.screen_width: int = self.screen().size().width()
        self.screen_height: int = self.screen().size().height()

        self.hasBeenUnderMousePreviousFrame: bool = False

        # spawning position
        cursorPos = QCursor.pos()
        center_x: int = cursorPos.x() - 50 # subtracting 50, as this is half of the width of the window (center it instead of top left)
        center_y: int = cursorPos.y() - 50

        self.move(center_x, center_y)
        self.posX = center_x
        self.posY = center_y

        # start the spawning anim!
        self.spawn_animation()
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            self.onMouseDown(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.onMouseUp(event)
        return False

    def onMouseDown(self, event):
        self.grabMouse()
        self.velX = 0
        self.velY = 0

        cursorPos = QCursor.pos()
        self.mouseOffsetX = self.posX - cursorPos.x()
        self.mouseOffsetY = self.posY - cursorPos.y()

        self.previousFramesX = [0, 0, 0, 0, 0, 0]
        self.previousFramesY = [0, 0, 0, 0, 0, 0]

        self.mouseDown = True
    
    def onMouseUp(self, event):
        self.releaseMouse()
        distancesX = []
        distancesY = []
        
        i = 0
        for frame in self.previousFramesX:
            if i == 0:
                i += 1
                continue

            try:
                distancesX.append((self.previousFramesX[i] - self.previousFramesX[i-1]) / (self.previousTimestamps[i] - self.previousTimestamps[i-1]))
            except Exception:
                distancesX.append(0)
            i += 1
        i = 0
        for frame in self.previousFramesY:
            if i == 0:
                i += 1
                continue
            try:
                distancesY.append((self.previousFramesY[i] - self.previousFramesY[i-1]) / (self.previousTimestamps[i] - self.previousTimestamps[i-1]))
            except Exception:
                distancesY.append(0)
            i += 1

        self.velX = sum(distancesX) / len(distancesX) / THROW_FACTOR
        self.velY = sum(distancesY) / len(distancesY) / THROW_FACTOR
        self.mouseDown = False

    def spawn_animation(self, i=1):
        current_time = time.perf_counter()
        delta_time = min(current_time - self.last_time, 0.05)
        self.last_time = current_time

        cursorPos = QCursor.pos()
        center_x = cursorPos.x() - 50 # subtracting 50, as this is half of the width of the window (center it instead of top left)
        center_y = cursorPos.y() - 50

        self.move((center_x + 50) - i // 2, (center_y + 50) - i // 2)
        self.setFixedSize(i, i)
        
        if i >= 100:
            i = 100
            self.setFixedSize(100, 100)
            self.posX: float = self.x()
            self.posY: float = self.y()
            QTimer.singleShot(16, self.update_physics)
        else:
            QTimer.singleShot(16, lambda: self.spawn_animation(i+int(250 * delta_time)))

    def check_window_collision(self): # TODO: i just copy pasted from the other script, so it no way works
        if not self.mouseDown:
            width = self.screen_width - self.width()
            height = self.screen_height - self.height()

            if self.posX < 0:
                distance = (self.posX - 0) / POP_FACTOR
                self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                self.posX = 0
            elif self.posX > width:
                distance = (self.posX - width) / POP_FACTOR
                self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                self.posX = width

            if self.posY > height:
                distance = (self.posY - height) / POP_FACTOR
                self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                self.posY = height
                if abs(self.velY) < 0.1:
                    self.velY = 0
            elif self.posY < 38:
                distance = (self.posY - 38) / POP_FACTOR
                self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                self.posY = 38
                if abs(self.velY) < 0.1:
                    self.velY = 0

    def update_physics(self):
        current_time = time.perf_counter()
        delta_time = min(current_time - self.last_time, 0.05)
        self.last_time = current_time

        if self.mouseDown:
            cursorPos = QCursor.pos()
            cursorX = cursorPos.x()
            cursorY = cursorPos.y()

            self.posX = cursorX + self.mouseOffsetX
            self.posY = cursorY + self.mouseOffsetY

            self.previousFramesX.append(cursorX)
            self.previousFramesY.append(cursorY)
            self.previousTimestamps.append(time.time())
            self.previousFramesX.pop(0)
            self.previousFramesY.pop(0)
            self.previousTimestamps.pop(0)
        else:
            self.velY += GRAVITY * delta_time
            self.velX -= self.velX / FRICTION * delta_time

            self.posX += self.velX
            self.posY += self.velY

        if not (self.x() == int(self.posX) and self.y() == int(self.posY)):
            if not self.mouseDown:
                if abs(self.velX) < 0.025:
                    self.velX = 0
                self.check_window_collision()
            self.move(int(self.posX), int(self.posY))

        QTimer.singleShot(8, self.update_physics)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    app.installEventFilter(win)
    win.show()
    app.exec()