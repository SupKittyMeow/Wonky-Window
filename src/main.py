import sys
from PySide6.QtWidgets import QApplication, QWidget, QSlider, QVBoxLayout, QLabel
from PySide6.QtGui import QCursor, QScreen
from PySide6.QtCore import QTimer, QEvent, Qt
from qframelesswindow import AcrylicWindow
import time
import os

if (sys.platform == 'linux'):
    os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

BOUNCE_FACTOR: int = 1
GRAVITY: int = 5
FRICTION: int = 3
THROW_FACTOR: int = 2
POP_FACTOR: int = 2
FPS = 60

refresh_rate = 60

# Class to handle the window stuff, such as the event handling and the settings stuff
class Window(AcrylicWindow):
    def __init__(self):        
        # basic setup stuff
        super().__init__()
        self.setWindowTitle('Wonky Window')
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

        self.state = 'loop'

        self.create_layout()
        
        # start the spawning anim!
        self.spawn_animation()
    
    def hide_from_alt_tab(self):
        if sys.platform == 'win32':
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

    def eventFilter(self, obj, event: QEvent):
        if event.type() == QEvent.Type.MouseButtonPress or event.type() == QEvent.Type.MouseButtonDblClick:
            self.onMouseDown(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.onMouseUp(event)
        if event.type() == QEvent.Type.Wheel:
            self.on_settings()
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

            self.velX = sum(distancesX) / len(distancesX) / (THROW_FACTOR * 100)
            self.velY = sum(distancesY) / len(distancesY) / (THROW_FACTOR * 100)
            
            self.mouseDown = False
    
    def on_gravity_change(self, value):
        global GRAVITY
        GRAVITY = value / 100
    def on_bounciness_change(self, value):
        global BOUNCE_FACTOR
        BOUNCE_FACTOR = value / 100
    def on_friction_change(self, value):
        global FRICTION
        FRICTION = value / 100
    def on_throw_factor_change(self, value):
        global THROW_FACTOR
        THROW_FACTOR = value / 100
    def on_pop_factor_change(self, value):
        global POP_FACTOR
        POP_FACTOR = value / 100
        
    def create_layout(self):
        self.new_layout = QVBoxLayout()

        self.gravity_layout = QVBoxLayout()
        self.gravity_layout.setContentsMargins(0, 0, 0, 30)
        self.gravity = QSlider(Qt.Orientation.Horizontal)
        self.gravity.setMinimum(1)
        self.gravity.setMaximum(1000)
        self.gravity.setValue(GRAVITY * 100)
        self.gravity.valueChanged.connect(self.on_gravity_change)
        self.gravity_layout.addWidget(self.gravity)

        self.gravity_label = QLabel('Gravity')
        self.gravity_layout.addWidget(self.gravity_label)

        self.new_layout.addLayout(self.gravity_layout)

        self.bounciness_layout = QVBoxLayout()
        self.bounciness_layout.setContentsMargins(0, 0, 0, 30)
        self.bounciness = QSlider(Qt.Orientation.Horizontal)
        self.bounciness.setMinimum(1)
        self.bounciness.setMaximum(500)
        self.bounciness.setValue(BOUNCE_FACTOR * 100)
        self.bounciness.valueChanged.connect(self.on_bounciness_change)
        self.bounciness_layout.addWidget(self.bounciness)
        
        self.bounciness_label = QLabel('Bounciness')
        self.bounciness_layout.addWidget(self.bounciness_label)

        self.new_layout.addLayout(self.bounciness_layout)

        self.friction_layout = QVBoxLayout()
        self.friction_layout.setContentsMargins(0, 0, 0, 30)
        self.friction = QSlider(Qt.Orientation.Horizontal)
        self.friction.setMinimum(1)
        self.friction.setMaximum(500)
        self.friction.setValue(FRICTION * 100)
        self.friction.valueChanged.connect(self.on_friction_change)
        self.friction_layout.addWidget(self.friction)
        
        self.friction_label = QLabel('Friction')
        self.friction_layout.addWidget(self.friction_label)

        self.new_layout.addLayout(self.friction_layout)

        self.throw_layout = QVBoxLayout()
        self.throw_layout.setContentsMargins(0, 0, 0, 30)
        self.throw = QSlider(Qt.Orientation.Horizontal)
        self.throw.setMinimum(100)
        self.throw.setMaximum(250)
        self.throw.setValue(THROW_FACTOR * 100)
        self.throw.valueChanged.connect(self.on_throw_factor_change)
        self.throw_layout.addWidget(self.throw)
        
        self.throw_label = QLabel('Throw power')
        self.throw_layout.addWidget(self.throw_label)
        
        self.new_layout.addLayout(self.throw_layout)
        
        self.new_layout.setSpacing(10)
        self.setLayout(self.new_layout)

    def show_sliders(self):
        self.gravity.show()
        self.gravity_label.show()
        self.bounciness.show()
        self.bounciness_label.show()
        self.friction.show()
        self.friction_label.show()
        self.throw.show()
        self.throw_label.show()
            
        self.hasBeenUnderMousePreviousFrame = False

        self.slide_in_effect()

    def slide_in_effect(self, scale=0):
        if scale >= 450:
            self.gravity.setFixedWidth(450)
            self.friction.setFixedWidth(450)
            self.bounciness.setFixedWidth(450)
            self.throw.setFixedWidth(450)
            return
        
        # Weird glitch if you go fast enough so show sliders every frame. TODO: fix better
        self.gravity.show()
        self.gravity_label.show()
        self.bounciness.show()
        self.bounciness_label.show()
        self.friction.show()
        self.friction_label.show()
        self.throw.show()
        self.throw_label.show()
        
        self.gravity.setFixedWidth(scale)
        self.bounciness.setFixedWidth(scale)
        self.friction.setFixedWidth(scale)
        self.throw.setFixedWidth(scale)
        QTimer.singleShot(16, lambda: self.slide_in_effect(scale+10))
    
    def hide_sliders(self, scale=450):
        if scale <= 0:
            self.gravity.setFixedWidth(0)
            self.friction.setFixedWidth(0)
            self.bounciness.setFixedWidth(0)
            self.throw.setFixedWidth(0)
            self.gravity.hide()
            self.gravity_label.hide()
            self.bounciness.hide()
            self.bounciness_label.hide()
            self.friction.hide()
            self.friction_label.hide()
            self.throw.hide()
            self.throw_label.hide()
            return
        self.gravity.setFixedWidth(scale)
        self.bounciness.setFixedWidth(scale)
        self.friction.setFixedWidth(scale)
        self.throw.setFixedWidth(scale)

        QTimer.singleShot(16, lambda: self.hide_sliders(scale-10))

    def animate_settings_open(self, center_x, center_y, i=0):
        if i > -400:
            self.posX = center_x + (100+i) / 2
            self.posY = center_y + (100+i*.75) / 2
            self.setFixedSize(int(100-i), (int(100-i*.75)))

            current_time = time.perf_counter()
            delta_time = min(current_time - self.last_time, 0.05)
            self.last_time = current_time
            
            QTimer.singleShot(16, lambda: self.animate_settings_open(center_x, center_y, i-int(500*delta_time)))
        else:
            self.setFixedSize(500, 400)
            # self.update_physics()
            self.state = 'settings'

    def animate_settings_close(self, center_x, center_y, i=0):
        if i < 400:
            self.posX = center_x - (int(500-i)) / 2
            self.posY = center_y - (int(400-i*.75) / 2)
            self.setFixedSize(int(500-i), (int(400-i*.75)))
            current_time = time.perf_counter()
            delta_time = min(current_time - self.last_time, 0.05)
            self.last_time = current_time
            QTimer.singleShot(16, lambda: self.animate_settings_close(center_x, center_y, i+int(500*delta_time)))
        else:
            self.setFixedSize(100, 100)
            # self.update_physics()
            self.state = 'loop'

    def on_settings(self, i=1):
        self.onMouseUp(False)
        self.velX = 0
        self.velY = 0
        if self.state == 'loop':
            self.state = 'opening settings'
            self.show_sliders()
            center_x = (self.posX + self.width() // 2) - 100
            center_y = (self.posY + self.height() // 2) - 100
            self.animate_settings_open(center_x=center_x, center_y=center_y)

        elif self.state == 'settings':
            self.state = 'closing settings'
            self.hide_sliders()
            center_x = (self.posX + self.width() // 2)
            center_y = (self.posY + self.height() // 2)
            self.animate_settings_close(center_x=center_x, center_y=center_y)


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

    def check_window_collision(self):
        print("check")
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
            if self.state == 'loop':
                current_time = time.perf_counter()
                delta_time = min(current_time - self.last_time, 0.05)
                self.last_time = current_time
                
                self.velY += GRAVITY * delta_time * self.screen().devicePixelRatio()
                self.velX -= self.velX / FRICTION * delta_time * self.screen().devicePixelRatio()

                self.posX += self.velX
                self.posY += self.velY

        if self.state == 'loop':
            if not (self.x() == int(self.posX) and self.y() == int(self.posY)):
                if not self.mouseDown:
                    if abs(self.velX) < 0.025:
                        self.velX = 0
                    self.check_window_collision()
        self.move(int(self.posX), int(self.posY))
        QTimer.singleShot(int(1000/refresh_rate), self.update_physics)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    refresh_rate = app.primaryScreen().refreshRate()

    wins: list[Window] = []
    for _ in range(1): # change this number to have different number of windows
        wins.append(Window())
    for win in wins:
        win.show()
        win.installEventFilter(win)
    app.exec()
