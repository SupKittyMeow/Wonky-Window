import tkinter
import time

BOUNCE_FACTOR = .77
GRAVITY = 0.1
FRICTION = 1.0125
THROW_FACTOR = 200
POP_FACTOR = 2

class Window:
    def __init__(self):
        self.root = tkinter.Tk()
        self.root.attributes('-topmost', True)
            
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        self.root.attributes('-alpha', 0.8)
        self.root.update_idletasks()
        self.root.geometry("{}x{}".format(1, 1))
        self.root.resizable(False, False)

        self.windowX = self.root.winfo_pointerx() - 50
        self.windowY = self.root.winfo_pointery() - 50
        self.mouseDown = False

        self.root.bind("<ButtonPress-1>", lambda event: self.MouseDown(True))
        self.root.bind("<ButtonRelease-1>", lambda event: self.MouseDown(False))
        self.root.bind('<Motion>', lambda event: self.Motion())
        self.velX = 0
        self.velY = 0

        self.offsetX = 0
        self.offsetY = 0

        self.previousFramesX = [0, 0, 0, 0, 0, 0]
        self.previousFramesY = [0, 0, 0, 0, 0, 0]
        self.previousTimestamps = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.animate_grow()
        self.root.mainloop()
        
    def MouseDown(self, down):
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

    def Motion(self):
        if (self.mouseDown):
            self.previousFramesX.append(self.root.winfo_pointerx())
            self.previousFramesY.append(self.root.winfo_pointery())
            self.previousTimestamps.append(time.time())
            self.previousFramesX.pop(0)
            self.previousFramesY.pop(0)
            self.previousTimestamps.pop(0)
            self.windowX = self.root.winfo_pointerx() + self.offsetX
            self.windowY = self.root.winfo_pointery() + self.offsetY
            self.CheckWindowStuff()
            self.root.geometry('+{}+{}'.format(self.root.winfo_pointerx() + self.offsetX, self.root.winfo_pointery() + self.offsetY))
            self.root.overrideredirect(True)

    def CheckWindowStuff(self):
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

    def Loop(self):
        if not self.mouseDown:
            self.windowX += self.velX
            self.windowY += self.velY
            self.CheckWindowStuff()
            self.root.geometry('+{}+{}'.format(int(self.windowX), int(self.windowY)))
            self.root.overrideredirect(True)
            self.velY += GRAVITY
            self.velX /= FRICTION

        self.root.after(8, self.Loop)

    def animate_grow(self, i=1):
        if i <= 50:
            center_x = self.root.winfo_pointerx() + 50
            center_y = self.root.winfo_pointery() + 50
            self.root.geometry('+{}+{}'.format(int(center_x - i - 50), int(center_y - i - 50)))
            self.root.geometry(f"{i*2}x{i*2}")

            self.root.overrideredirect(True)
            
            self.root.after(10, self.animate_grow, i+1)
        else:
            self.windowX = self.root.winfo_x()
            self.windowY = self.root.winfo_y()
            self.Loop()

window = Window()