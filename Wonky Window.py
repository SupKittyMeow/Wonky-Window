import sys
import tkinter as tk
import tkinter.ttk as ttk
import time

BOUNCE_FACTOR = .88
GRAVITY = 0.1
FRICTION = 1.0125
THROW_FACTOR = 200
POP_FACTOR = 2

class Window:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.lift()
        self.root.attributes('-topmost', True)
            
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.hasBeenUnderMousePreviousFrame = False

        self.root.attributes('-alpha', 0.8)
        self.root.update_idletasks()
        self.root.geometry('{}x{}'.format(1, 1))
        self.root.resizable(False, False)

        self.root.title("Wonky Window")

        if sys.platform == "darwin": # macos
            self.root.createcommand(
                'tk::mac::ShowPreferences',
                self.on_settings
            )
            self.root['menu'] = tk.Menu(self.root)
        else:
            menubar = tk.Menu(self.root)
            settings_menu = tk.Menu(menubar, tearoff=0)
            settings_menu.add_command(label="Settings", command=self.on_settings,
                                      accelerator="Ctrl+,")
            menubar.add_cascade(label="Settings", menu=settings_menu)
            self.root['menu'] = menubar

        self.windowX = self.root.winfo_pointerx() - 50
        self.windowY = self.root.winfo_pointery() - 50
        self.mouseDown = False

        self.root.bind('<ButtonPress-1>', lambda event: self.mouse_down(True))
        self.root.bind('<ButtonRelease-1>', lambda event: self.mouse_down(False))
        self.root.bind('<Motion>', lambda event: self.motion())

        self.root.bind('<Control-comma>', lambda event: self.on_settings())
        self.root.bind('<Command-comma>', lambda event: self.on_settings())

        self.velX = 0
        self.velY = 0

        self.offsetX = 0
        self.offsetY = 0

        self.previousFramesX = [0, 0, 0, 0, 0, 0]
        self.previousFramesY = [0, 0, 0, 0, 0, 0]
        self.previousTimestamps = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.root.lift()
        self.state = "growing"
        self.animate_grow()
        self.root.mainloop()

    def mouse_down(self, down):
        if hasattr(self, 'gravity') or hasattr(self, 'bounciness') or hasattr(self, 'friction'):
            widget_under_mouse = self.root.winfo_containing(self.root.winfo_pointerx(), self.root.winfo_pointery())
            if widget_under_mouse == self.gravity or widget_under_mouse == self.bounciness or widget_under_mouse == self.friction:
                self.hasBeenUnderMousePreviousFrame = True
                
        if self.mouseDown == False and down == True:
            self.velX = 0
            self.velY = 0
            self.previousFramesX = [0, 0, 0, 0, 0, 0]
            self.previousFramesY = [0, 0, 0, 0, 0, 0]
        self.mouseDown = down
        self.offsetX = self.root.winfo_rootx() - self.root.winfo_pointerx()
        self.offsetY = self.root.winfo_rooty() - self.root.winfo_pointery()

        if not down:
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

    def motion(self):
        if self.mouseDown == False:
            self.hasBeenUnderMousePreviousFrame = False
        if (self.mouseDown and not self.hasBeenUnderMousePreviousFrame):
            self.previousFramesX.append(self.root.winfo_pointerx())
            self.previousFramesY.append(self.root.winfo_pointery())
            self.previousTimestamps.append(time.time())
            self.previousFramesX.pop(0)
            self.previousFramesY.pop(0)
            self.previousTimestamps.pop(0)
            self.windowX = self.root.winfo_pointerx() + self.offsetX
            self.windowY = self.root.winfo_pointery() + self.offsetY
            self.check_window_collision()
            self.root.geometry('+{}+{}'.format(self.root.winfo_pointerx() + self.offsetX, self.root.winfo_pointery() + self.offsetY))
            self.root.overrideredirect(True)
    
    def on_gravity_change(self, value):
        global GRAVITY
        GRAVITY = float(value)

    def on_bounciness_change(self, value):
        global BOUNCE_FACTOR
        BOUNCE_FACTOR = float(value)

    def on_friction_change(self, value):
        global FRICTION
        FRICTION = float(value)
    
    def on_throw_factor_change(self, value):
        global THROW_FACTOR
        THROW_FACTOR = float(value)

    def on_pop_factor_change(self, value):
        global POP_FACTOR
        POP_FACTOR = float(value)

    def show_sliders(self):
        self.hasBeenUnderMousePreviousFrame = False

        self.gravity = ttk.Scale(self.root, from_=0, to=2, orient='horizontal', length=300, command=self.on_gravity_change)
        self.gravity.set(GRAVITY)
        self.gravity.pack(expand=True, pady=(25, 0))
        self.gravity_label = tk.Label(self.root, text="Gravity")
        self.gravity_label.pack(pady=(0, 50))  

        self.bounciness = ttk.Scale(self.root, from_=0, to=1, orient='horizontal', length=300, command=self.on_bounciness_change)
        self.bounciness.set(BOUNCE_FACTOR)
        self.bounciness.pack(expand=True)
        self.bounciness_label = tk.Label(self.root, text="Bounciness")
        self.bounciness_label.pack(pady=(0, 50))

        self.friction = ttk.Scale(self.root, from_=1, to=1.2, orient='horizontal', length=300, command=self.on_friction_change)
        self.friction.set(FRICTION)
        self.friction.pack(expand=True)
        self.friction_label = tk.Label(self.root, text="Friction")
        self.friction_label.pack(pady=(0, 25))

        self.slide_in_effect()

    def slide_in_effect(self, scale=0.0):
        if scale >= 300:
            self.gravity.configure(length=300)
            self.friction.configure(length=300)
            self.bounciness.configure(length=300)
            return
        self.gravity.configure(length=scale)
        self.bounciness.configure(length=scale)
        self.friction.configure(length=scale)
        self.root.after(1, self.slide_in_effect, scale+2)
    
    def hide_sliders(self, scale=300):
        if scale <= 0:
            self.gravity.destroy()
            self.gravity_label.destroy()
            self.bounciness.destroy()
            self.bounciness_label.destroy()
            self.friction.destroy()
            self.friction_label.destroy()
            return
        self.gravity.configure(length=scale)
        self.bounciness.configure(length=scale)
        self.friction.configure(length=scale)

        self.root.after(1, self.hide_sliders, scale-2)

    def animate_settings_open(self, center_x, center_y, i=0):
        if i < 400:
            self.root.geometry('+{}+{}'.format(int(center_x - (int(100+i)) / 2), int(center_y - (int(100+i*.5) / 2))))
            self.root.geometry(f'{int(100+i)}x{int(100+i*.5)}')
            self.root.after(10, self.animate_settings_open, center_x, center_y, i+10)
            self.root.overrideredirect(True)
        else:
            self.root.geometry(f'500x300')
            self.root.update()
            self.state = "settings"
            self.root.overrideredirect(True)

    def animate_settings_close(self, center_x, center_y, i=0):
        if i < 400:
            self.root.geometry('+{}+{}'.format(int(center_x - (int(500-i)) / 2), int(center_y - (int(300-i*.5) / 2))))
            self.root.geometry(f'{int(500-i)}x{int(300-i*.5)}')
            self.root.after(10, self.animate_settings_close, center_x, center_y, i+10)
            self.root.overrideredirect(True)
        else:
            self.root.geometry(f'100x100')
            self.root.update()
            self.state = "loop"
            self.root.overrideredirect(True)

    def on_settings(self, i=1):
        self.mouse_down(False)
        self.velX = 0
        self.velY = 0
        if self.state == "loop":
            self.state = "opening settings"
            self.show_sliders()
            center_x = self.windowX + 50
            center_y = self.windowY + 50
            self.animate_settings_open(center_x=center_x, center_y=center_y)

        elif self.state == "settings":
            self.state = "closing settings"
            self.hide_sliders()
            self.windowX = (self.root.winfo_rootx() + self.root.winfo_width() // 2) - 50
            self.windowY = (self.root.winfo_rooty() + self.root.winfo_height() // 2) - 50
            center_x = self.windowX + 50
            center_y = self.windowY + 50
            self.animate_settings_close(center_x=center_x, center_y=center_y)

    def check_window_collision(self):
        if self.state == "loop":
            if not self.mouseDown:
                width = self.screen_width - self.root.winfo_width()
                height = self.screen_height - self.root.winfo_height()

                if self.windowX < 0:
                    distance = round(self.windowX - 0) / POP_FACTOR
                    self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                    self.windowX = 0
                elif self.windowX > width:
                    distance = round(self.windowX - width) / POP_FACTOR
                    self.velX = (-self.velX * BOUNCE_FACTOR) + distance
                    self.windowX = width

                if self.windowY > height:
                    distance = round(self.windowY - height) / POP_FACTOR
                    self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                    self.windowY = height
                elif self.windowY < 38:
                    distance = round(self.windowY - 38) / POP_FACTOR
                    self.velY = (-self.velY * BOUNCE_FACTOR) + distance
                    self.windowY = 38

    def loop(self):
        if self.state == "loop":
            if not self.mouseDown:
                self.windowX += self.velX
                self.windowY += self.velY
                self.check_window_collision()
                self.root.geometry('+{}+{}'.format(int(self.windowX), int(self.windowY)))
                self.root.overrideredirect(True)
                self.velY += GRAVITY
                self.velX /= FRICTION

        self.root.after(8, self.loop)

    def animate_grow(self, i=1):
        if i <= 50:
            center_x = self.root.winfo_pointerx()
            center_y = self.root.winfo_pointery()
            self.root.geometry('+{}+{}'.format(int(center_x - i), int(center_y - i)))
            self.root.geometry(f'{i*2}x{i*2}')
            self.root.overrideredirect(True)
            
            self.root.after(10, self.animate_grow, i+1)
        else:
            self.windowX = self.root.winfo_x()
            self.windowY = self.root.winfo_y()
            self.state = "loop"
            self.loop()

window = Window()