import sys
from PySide6.QtWidgets import QApplication, QWidget, QSlider, QVBoxLayout, QComboBox, QLabel, QFrame
from PySide6.QtGui import QCursor, QEnterEvent, QScreen, QWheelEvent
from PySide6.QtCore import QTimer, QEvent, Qt, QPoint
from qframelesswindow import AcrylicWindow
import time
import os
import numpy as np

if (sys.platform == 'linux'):
    os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')

BOUNCE_FACTOR: float = 0.8
GRAVITY: float = 4.15
FRICTION: float = 0.3
THROW_POWER: float = 0.5
POP_FACTOR: float = 2

refresh_rate = 60
isBlurred = True

# Class to handle the window stuff, such as the event handling and the settings stuff
class Window(AcrylicWindow):
    def __init__(self, winIndex=0, maxWins=1):
        # basic setup stuff
        super().__init__()
    
        self.setWindowTitle('Wonky Window')
        
        self.setFixedSize(1, 1)
        self.setResizeEnabled(False)

        self.window_widget = QWidget()
        self.setTitleBar(self.window_widget) # don't use self.titleBar.hide() here because this takes full screen and lets focus be IMMEDIATELY grabbed

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
        
        self.mouseOverSlider = False
        
        self.winIndex = winIndex
        self.maxWins = maxWins
        
        # spawning position
        cursorPos = QCursor.pos()
        center_x: int = (cursorPos.x() - 50) + ((winIndex-maxWins*2) * 110)
        center_y: int = (cursorPos.y() - 50) # subtracting 50, as this is half of the width of the window (center it instead of top left)

        self.move(center_x, center_y)
        self.posX = center_x
        self.posY = center_y

        self.wasMouseDown = False
        
        window = self.windowHandle()
        if window is not None:
            window.screenChanged.connect(self.screen_changed)

        self.screen_changed(self.screen())

        self.state = 'spawn_animation'

        self.create_layout()

        self.setAcrylicEffectEnabled(False, 0.8)

        # start the spawning anim!
        self.spawn_animation()
    
    def setAcrylicEffectEnabled(self, enable: bool, opacity=1.0):
        """ set acrylic effect enabled """
        self.setStyleSheet(f"background:{'transparent' if enable else "#1e1f1f"}")
        self.setWindowOpacity(opacity)
        
        if enable:
            self.windowEffect.setAcrylicEffect(self.winId(), "7D7D7D")
            # self.windowEffect.removeShadowEffect(self.winId())
        else:
            self.windowEffect.setAcrylicEffect(self.winId(), "7D7D7D")
            # self.windowEffect.removeShadowEffect(self.winId())
            self.windowEffect.removeBackgroundEffect(self.winId())

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

    def wheelEvent(self, event: QWheelEvent):
        if event.phase() == Qt.ScrollPhase.ScrollBegin:
            self.on_settings()
            event.accept()
        elif event.phase() == Qt.ScrollPhase.ScrollEnd:
            event.accept()
        elif event.phase() == Qt.ScrollPhase.ScrollUpdate:
            event.accept()
        elif event.phase() == Qt.ScrollPhase.ScrollMomentum:
            event.accept()
        else: # hopefully a working fallback for devices that don't support scroll phases (mice, etc)
            self.on_settings()
            event.accept()
            
    def eventFilter(self, obj, event: QEvent):
        if event.type() == QEvent.Type.MouseButtonPress or event.type() == QEvent.Type.MouseButtonDblClick:
            if not self.mouseOverSlider: self.onMouseDown(event)
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if not self.mouseOverSlider: self.onMouseUp(event)
        if event.type() == QEvent.Type.Close:
            self.state = 'closing'
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
            for _ in self.previousFramesY:
                if i == 0:
                    i += 1
                    continue
                try:
                    distancesY.append((self.previousFramesY[i] - self.previousFramesY[i-1]) / (self.previousTimestamps[i] - self.previousTimestamps[i-1]))
                except Exception:
                    distancesY.append(0)
                i += 1

            self.velX = sum(distancesX) / len(distancesX) * THROW_POWER / 100
            self.velY = sum(distancesY) / len(distancesY) * THROW_POWER / 100
            
            self.mouseDown = False
    
    def on_gravity_change(self, value):
        global GRAVITY
        if value == 0: GRAVITY = 0
        GRAVITY = value / 100
    def on_bounciness_change(self, value):
        global BOUNCE_FACTOR
        if value == 0: BOUNCE_FACTOR = 0
        BOUNCE_FACTOR = value / 100
    def on_friction_change(self, value):
        global FRICTION
        if value == 0: FRICTION = 0
        FRICTION = value / 100
        
    def on_throw_factor_change(self, value):
        global THROW_POWER
        if value == 0: THROW_POWER = 0
        THROW_POWER = value / 100
    def on_pop_factor_change(self, value):
        global POP_FACTOR
        if value == 0: POP_FACTOR = 0
        POP_FACTOR = value / 100
        
    def on_blur_changed(self, value):
        if value == 0:
            self.setAcrylicEffectEnabled(False, 0.8)
        elif value == 1:
            self.setAcrylicEffectEnabled(True)
        else:
            self.setAcrylicEffectEnabled(False, 1)
            
        # 0 = default
        # 1 = blurred
        # 2 = solid
        
    class BetterSlider(QSlider):
        """A slider without scroll input.

        Args:
            QSlider (_type_): _description_
        """
        def wheelEvent(self, event: QWheelEvent):
            event.ignore()
        
        def enterEvent(self, event: QEnterEvent) -> None:
            self.parent().mouseOverSlider = True # type: ignore
            event.accept()
            
        def leaveEvent(self, event: QEnterEvent) -> None:
            self.parent().mouseOverSlider = False # type: ignore
            event.accept()
            
    def create_layout(self):
        self.new_layout = QVBoxLayout()

        self.gravity_layout = QVBoxLayout()
        self.gravity_layout.setContentsMargins(0, 0, 0, 30)
        self.gravity = self.BetterSlider(Qt.Orientation.Horizontal)
        self.gravity.setMinimum(0)
        self.gravity.setMaximum(3000)
        self.gravity.setValue(int(GRAVITY * 100))
        self.gravity.valueChanged.connect(self.on_gravity_change)
        self.gravity_layout.addWidget(self.gravity)

        self.gravity_label = QLabel('Gravity')

        self.gravity_layout.addWidget(self.gravity_label)

        self.new_layout.addLayout(self.gravity_layout)

        self.bounciness_layout = QVBoxLayout()
        self.bounciness_layout.setContentsMargins(0, 0, 0, 30)
        self.bounciness = self.BetterSlider(Qt.Orientation.Horizontal)
        self.bounciness.setMinimum(0)
        self.bounciness.setMaximum(100)
        self.bounciness.setValue(int(BOUNCE_FACTOR * 100))
        self.bounciness.valueChanged.connect(self.on_bounciness_change)
        self.bounciness_layout.addWidget(self.bounciness)
        
        self.bounciness_label = QLabel('Bounciness')
        self.bounciness_layout.addWidget(self.bounciness_label)

        self.new_layout.addLayout(self.bounciness_layout)

        self.friction_layout = QVBoxLayout()
        self.friction_layout.setContentsMargins(0, 0, 0, 30)
        self.friction = self.BetterSlider(Qt.Orientation.Horizontal)
        self.friction.setMinimum(0)
        self.friction.setMaximum(200)
        self.friction.setValue(int(FRICTION * 100))
        self.friction.valueChanged.connect(self.on_friction_change)
        self.friction_layout.addWidget(self.friction)
        
        self.friction_label = QLabel('Friction')
        self.friction_layout.addWidget(self.friction_label)

        self.new_layout.addLayout(self.friction_layout)

        self.throw_layout = QVBoxLayout()
        self.throw_layout.setContentsMargins(0, 0, 0, 30)
        self.throw = self.BetterSlider(Qt.Orientation.Horizontal)
        self.throw.setMinimum(0)
        self.throw.setMaximum(300)
        self.throw.setValue(int(THROW_POWER * 100))
        self.throw.valueChanged.connect(self.on_throw_factor_change)
        self.throw_layout.addWidget(self.throw)
        
        self.throw_label = QLabel('Throw power')
        self.throw_layout.addWidget(self.throw_label)
        
        self.new_layout.addLayout(self.throw_layout)
        
        self.blur_layout = QVBoxLayout()
        self.blur_layout.setContentsMargins(0, 0, 0, 30)
        self.blur = QComboBox()
        self.blur.addItem("Translucent (Default)")
        self.blur.addItem("Blurred (WARNING: Can be laggy)")
        self.blur.addItem("Solid")
        
        self.blur.currentIndexChanged.connect(self.on_blur_changed)
        self.blur_layout.addWidget(self.blur)
        
        self.blur_label = QLabel('Blur type')
        self.blur_layout.addWidget(self.blur_label)
        
        self.new_layout.addLayout(self.blur_layout)
        
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
        self.blur.show()
        self.blur_label.show()
    
    def hide_sliders(self):
        self.gravity.hide()
        self.gravity_label.hide()
        self.bounciness.hide()
        self.bounciness_label.hide()
        self.friction.hide()
        self.friction_label.hide()
        self.throw.hide()
        self.throw_label.hide()
        self.blur.hide()
        self.blur_label.hide()

    def animate_settings_open(self, center_x, center_y, i: float = 0):
        if i <= 4:
            self.posX = center_x + (100-i*100) / 2
            self.posY = center_y + (100-i*100) / 2
            self.setFixedSize(int(100+i*100), (int(100+i*100)))

            current_time = time.perf_counter()
            delta_time = min(current_time - self.last_time, 0.05)
            self.last_time = current_time
            
            QTimer.singleShot(int(1000 / refresh_rate), lambda: self.animate_settings_open(center_x, center_y, i + (delta_time * 7.5)))
        else:
            self.setFixedSize(500, 500)
            self.state = 'settings'

    def animate_settings_close(self, center_x, center_y, i: float = 0):
        if i < 4:
            self.mouseOverSlider = False
            self.posX = center_x - (int(500-i*100)) / 2
            self.posY = center_y - (int(500-i*100) / 2)
            self.setFixedSize(int(500-i*100), (int(500-i*100)))
            
            current_time = time.perf_counter()
            delta_time = min(current_time - self.last_time, 0.05)
            self.last_time = current_time
            
            QTimer.singleShot(int(1000 / refresh_rate), lambda: self.animate_settings_close(center_x, center_y, i + (delta_time * 7.5)))
        else:
            self.hide_sliders()
            self.setFixedSize(100, 100)
            self.state = 'loop'

    def on_settings(self, i=1):
        self.onMouseUp(False)
        self.velX = 0
        self.velY = 0
        if self.state == 'loop':
            self.state = 'opening settings'
            center_x = (self.posX + self.width() // 2) - 100
            center_y = (self.posY + self.height() // 2) - 100
            self.show_sliders()
            self.animate_settings_open(center_x=center_x, center_y=center_y)

        elif self.state == 'settings':
            self.state = 'closing settings'
            center_x = (self.posX + self.width() // 2)
            center_y = (self.posY + self.height() // 2)
            self.animate_settings_close(center_x=center_x, center_y=center_y)


    def spawn_animation(self, i: float = 0.01):
        self.state = 'spawn_animation'
        cursorPos = QCursor.pos()
        center_x: int = (cursorPos.x() - 50)
        center_y = cursorPos.y() - 50

        self.move(int((center_x + 50) + ((self.winIndex-self.maxWins*2) * 150) - (i * 100) / 2), int((center_y + 50) - (i * 100) / 2))
        self.setFixedSize(int(i * 100), int(i * 100))
        
        current_time = time.perf_counter()
        delta_time = min(current_time - self.last_time, 0.05)
        self.last_time = current_time
        
        if i >= 1:
            i = 1
            self.setFixedSize(100, 100)
            self.posX: float = self.x()
            self.posY: float = self.y()
            self.state = 'loop'
            QTimer.singleShot(int(1000 / refresh_rate), self.update_physics)
        else:
            QTimer.singleShot(int(1000 / refresh_rate), lambda: self.spawn_animation(i + (delta_time * 2)))

    def screen_changed(self, screen: QScreen):
        global refresh_rate
        refresh_rate = screen.refreshRate()
        self.geo = screen.availableGeometry()

    def check_window_collision(self):
        if not self.mouseDown:
            furthestLeft = self.geo.left()
            furthestUp = self.geo.top()
            width = self.geo.right() - self.width()
            height = self.geo.bottom() - self.height()
            posX = self.posX
            posY = self.posY
            oldVelX = self.velX
            oldVelY = self.velY
            didHitH = False
            didHitV = False
            
            if posX < furthestLeft:
                distance = (posX - furthestLeft) / POP_FACTOR
                self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                posX = furthestLeft
                didHitH = True
            elif posX > width:
                distance = (posX - width) / POP_FACTOR
                self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                didHitH = True
                posX = width

            if posY > height:
                distance = (posY - height) / POP_FACTOR
                self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                didHitV = True
                posY = height
                if abs(self.velY) < 0.1:
                    self.velY = 0
            elif posY < furthestUp:
                distance = (posY - furthestUp) / POP_FACTOR
                self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                didHitV = True
                posY = furthestUp
                if abs(self.velY) < 0.1:
                    self.velY = 0

            if not self.wasMouseDown:
                if didHitH:
                    self.velX = -oldVelX * BOUNCE_FACTOR
                if didHitV:
                    if abs(oldVelY) < 1:
                        self.velY = 0
                    else:
                        self.velY = -oldVelY * BOUNCE_FACTOR
                    
            self.posX = posX
            self.posY = posY

    def collision_with_other_window(self, coll: Window):
        dx = (self.posX + self.size().width() / 2) - (coll.posX + coll.size().width() / 2)
        dy = (self.posY + self.size().height() / 2) - (coll.posY + coll.size().height() / 2)
        overlapX = ((self.size().width() / 2) + (coll.size().width() / 2)) - abs(dx)
        overlapY = ((self.size().height() / 2) + (coll.size().height() / 2)) - abs(dy)
        collision_normal = (0, 0)
        if overlapX < overlapY: # More overlapped on horizontal than vertical, meaning flip on vertical
            if dx == 0:
                dx = 1 # Fallback
            collision_normal = (np.sign(dx), 0)
        else:
            if dy == 0:
                dy = 1 # Fallback
            collision_normal = (0, np.sign(dy))

        speed_along_normal = np.dot((self.velX, self.velY), collision_normal) # Velocity scalar
        velocity_along_normal = np.array([collision_normal[0] * speed_along_normal, collision_normal[1] * speed_along_normal]) # Projected velocity vector along normal
        tangent_velocity = np.array((self.velX, self.velY)) - velocity_along_normal # Perpendicular velocity vector along normal
        self.velX = tangent_velocity[0]
        self.velY = tangent_velocity[1]

    def do_velocity_stuff(self):
        current_time = time.perf_counter()
        delta_time = min(current_time - self.last_time, 0.05)
        self.last_time = current_time
        
        self.velY += GRAVITY * delta_time * self.screen().devicePixelRatio()
        self.velX -= self.velX * FRICTION * delta_time * self.screen().devicePixelRatio()
        self.posX += self.velX
        self.posY += self.velY

    def do_move_stuff(self):
        if self.state == 'loop':
                    if not (self.x() == int(self.posX) and self.y() == int(self.posY)):
                        if not self.mouseDown:
                            if abs(self.velX) < 0.025:
                                self.velX = 0
                            self.check_window_collision()
                            self.wasMouseDown = False
        if not (self.velX == 0 and self.velY == 0) or self.mouseDown or self.state != 'loop': # optimization to prevent redrawing EVERY SINGLE FRAME even if it hasn't moved
            self.move(int(self.posX), int(self.posY))

    def update_physics(self):
        if self.state == 'closing':
            QApplication.quit()
            return
        
        if self.mouseDown:
            cursorPos = QCursor.pos()
            cursorX = cursorPos.x()
            cursorY = cursorPos.y()

            self.wasMouseDown = True
            
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
                self.do_velocity_stuff()

        self.do_move_stuff()

def collide_window_logic(fw: Window, sw: Window):
    # Top left collision
    fwS = fw.size().width()

    swS = sw.size().width() / 2
    swPos = sw.pos()
    swPos.setX(swPos.x() + int(swS))
    swPos.setY(swPos.y() - int(swS))

    
    tl = QPoint(int(fw.posX), int(fw.posY))
    bl = QPoint(int(fw.posX), int(fw.posY + fwS))
    tr = QPoint(int(fw.posX + fwS), int(fw.posY))
    br = QPoint(int(fw.posX), int(fw.posY - fwS))

    corners = [tl, bl, tr, bl, br]
    for corner in corners:
        if abs(corner.x() - swPos.x()) < swS: # Check collision horizontal
            if abs(corner.y() - swPos.y()) < swS: # Check collision vertical
                fw.collision_with_other_window(sw)
                sw.collision_with_other_window(fw)

def loop_window_check():
    i = 0
    for win in wins:
        win.update_physics()
        j = 0
        for collision in wins:
            if j <= i:
                j += 1
                continue
            else:
                collide_window_logic(win, collision)
            j += 1
        i += 1
    QTimer.singleShot(16, loop_window_check)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    refresh_rate = app.primaryScreen().refreshRate()

    wins: list[Window] = []
    for i in range(5): # change this number to have different number of windows
        wins.append(Window(i))
    for win in wins:
        win.show()
        win.installEventFilter(win)
    loop_window_check()
    app.exec()