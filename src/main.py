import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QCursor, QScreen
from PySide6.QtCore import QTimer, QEvent, Qt
from qframelesswindow import AcrylicWindow
import time
import os

if (sys.platform == 'linux'):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

BOUNCE_FACTOR = 1
GRAVITY = 5
FRICTION = 3
THROW_FACTOR = 200
POP_FACTOR = 2
FPS = 60

refresh_rate = 60

# Class to handle the window stuff, such as the event handling and the settings stuff
class Window(AcrylicWindow):
    def __init__(self):        
        # basic setup stuff
        super().__init__()
        self.setWindowTitle("Wonky Window")
        self.setFixedSize(1, 1)
        self.setResizeEnabled(False)

        self.setTitleBar(QWidget()) # don't use self.titleBar.hide() here because this takes full screen and lets focus be IMMEDIATELY grabbed

        self.toggleStayOnTop()

        self.hide_from_alt_tab()        
        
        # updating vars setup
        self.last_time: float = time.perf_counter()
        self.velX: float = 0 
        self.velY: float = 0
        self.posX: float = 0
        self.posY: float = 0

        self.screen_offsetX = 0
        self.screen_offsetY = 0
        self.previousFramesX = [0, 0, 0, 0, 0, 0]
        self.previousFramesY = [0, 0, 0, 0, 0, 0]
        self.previousTimestamps = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.mouseDown: bool = False
        
        self.screen_width: int = self.screen().availableSize().width()
        self.screen_height: int = self.screen().availableSize().height()

        self.hasBeenUnderMousePreviousFrame: bool = False

        # spawning position
        cursorPos = QCursor.pos()
        center_x: int = cursorPos.x() - 50 # subtracting 50, as this is half of the width of the window (center it instead of top left)
        center_y: int = cursorPos.y() - 50

        self.move(center_x, center_y)
        self.posX = center_x
        self.posY = center_y

        window = self.windowHandle()
        if window is not None:
            window.screenChanged.connect(self.screen_changed)

        self.screen_changed(self.screen())

        # start the spawning anim!
        self.spawn_animation()
    
    def hide_from_alt_tab(self):
        if sys.platform == "win32":
            import ctypes
            hwnd = self.winId()
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_APPWINDOW = 0x00040000
            user32 = ctypes.windll.user32
            current_style = user32.GetWindowLongPtrA(hwnd, GWL_EXSTYLE)
            new_style = (current_style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
            user32.SetWindowLongPtrA(hwnd, GWL_EXSTYLE, new_style)
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0023)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            self.onMouseDown(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.onMouseUp(event)
        if event.type() == QEvent.Type.Close:
            QApplication.quit()
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
        self.previousTimestamps = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.mouseDown = True

    def onMouseUp(self, event):
        self.releaseMouse()

        if self.mouseDown:
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
            current_time = time.perf_counter()
            delta_time = min(current_time - self.last_time, 0.05)
            self.last_time = current_time
            QTimer.singleShot(16, lambda: self.spawn_animation(i+int(250 * delta_time)))

    def screen_changed(self, screen: QScreen):
        self.geo = screen.availableGeometry()
        # self.screen_width: int = geo.width()
        # self.screen_height: int = geo.height()
        # self.screen_offsetX: int = geo.x()
        # self.screen_offsetY: int = geo.y()

    def check_window_collision(self):
        if not self.mouseDown:
            self.screen_changed(self.screen())
            furthestLeft = self.geo.left()
            furthestUp = self.geo.top()
            width = self.geo.right() - self.width()
            height = self.geo.bottom() - self.height()
            posX = self.posX
            posY = self.posY
            
            if posX < furthestLeft:
                distance = (posX - furthestLeft) / POP_FACTOR
                self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                posX = furthestLeft
            elif posX > width:
                distance = (posX - width) / POP_FACTOR
                self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                posX = width

            if posY > height:
                distance = (posY - height) / POP_FACTOR
                self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                posY = height
                if abs(self.velY) < 0.1:
                    self.velY = 0
            elif posY < furthestUp:
                distance = (posY - furthestUp) / POP_FACTOR
                self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                posY = furthestUp
                if abs(self.velY) < 0.1:
                    self.velY = 0

            self.posX = posX
            self.posY = posY

    def update_physics(self):
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
            current_time = time.perf_counter()
            delta_time = min(current_time - self.last_time, 0.05)
            self.last_time = current_time
            
            self.velY += GRAVITY * delta_time * self.screen().devicePixelRatio()
            self.velX -= self.velX / FRICTION * delta_time * self.screen().devicePixelRatio()

            self.posX += self.velX
            self.posY += self.velY

        if not (self.x() == int(self.posX) and self.y() == int(self.posY)):
            if not self.mouseDown:
                if abs(self.velX) < 0.025:
                    self.velX = 0
                self.check_window_collision()
            self.move(int(self.posX), int(self.posY))
        QTimer.singleShot(int(1000/refresh_rate), self.update_physics)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    refresh_rate = app.primaryScreen().refreshRate()

    wins: list[Window] = []
    for _ in range(1): # change this number to have different number of windows
        wins.append(Window())
    for win in wins:
        win.show()
        win.installEventFilter(win)
    app.exec()
