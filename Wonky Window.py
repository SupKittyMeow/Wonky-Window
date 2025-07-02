import tkinter
import time

BOUNCE_FACTOR = .77
GRAVITY = 0.1
FRICTION = 1.0125
THROW_FACTOR = 200
POP_FACTOR = 2

root = tkinter.Tk()
root.attributes('-topmost', True)

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.attributes('-alpha', 0.8)
root.update_idletasks()
root.geometry("{}x{}".format(1, 1))
root.resizable(False, False)

windowX = root.winfo_pointerx() - 50
windowY = root.winfo_pointery() - 50
mouseDown = False

root.bind("<ButtonPress-1>", lambda event: MouseDown(True))
root.bind("<ButtonRelease-1>", lambda event: MouseDown(False))
root.bind('<Motion>', lambda event: Motion())

velX = 0
velY = 0

offsetX = 0
offsetY = 0

previousFramesX = [0, 0, 0, 0, 0, 0]
previousFramesY = [0, 0, 0, 0, 0, 0]
previousTimestamps = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

def MouseDown(down):
    global mouseDown, offsetX, offsetY, previousFramesX, previousFramesY, velX, velY

    if mouseDown == False and down == True:
        velX = 0
        velY = 0
        previousFramesX = [0, 0, 0, 0, 0, 0]
        previousFramesY = [0, 0, 0, 0, 0, 0]
    mouseDown = down
    offsetX = root.winfo_rootx() - root.winfo_pointerx()
    offsetY = root.winfo_rooty() - root.winfo_pointery()

    if not down:
        distancesX = []
        distancesY = []
        
        i = 0
        for frame in previousFramesX:
            if i == 0:
                i += 1
                continue

            try:
                distancesX.append((previousFramesX[i] - previousFramesX[i-1]) / (previousTimestamps[i] - previousTimestamps[i-1]))
            except Exception:
                distancesX.append(0)
            i += 1
        i = 0
        for frame in previousFramesY:
            if i == 0:
                i += 1
                continue
            try:
                distancesY.append((previousFramesY[i] - previousFramesY[i-1]) / (previousTimestamps[i] - previousTimestamps[i-1]))
            except Exception:
                distancesY.append(0)
            i += 1

        velX = sum(distancesX) / len(distancesX) / THROW_FACTOR
        velY = sum(distancesY) / len(distancesY) / THROW_FACTOR

def Motion():
    if (mouseDown):
        global velX, velY, offsetX, offsetY, windowX, windowY, previousFramesX, previousFramesY
        previousFramesX.append(root.winfo_pointerx())
        previousFramesY.append(root.winfo_pointery())
        previousTimestamps.append(time.time())
        previousFramesX.pop(0)
        previousFramesY.pop(0)
        previousTimestamps.pop(0)
        windowX = root.winfo_pointerx() + offsetX
        windowY = root.winfo_pointery() + offsetY
        CheckWindowStuff()
        root.geometry('+{}+{}'.format(root.winfo_pointerx() + offsetX, root.winfo_pointery() + offsetY))
        root.overrideredirect(True)

def CheckWindowStuff():
    if not mouseDown:
        global windowX, windowY, velX, velY

        width = screen_width - root.winfo_width()
        height = screen_height - root.winfo_height()

        if windowX < 0:
            distance = round(windowX - 0) / POP_FACTOR
            velX = (-velX * BOUNCE_FACTOR) + distance
            windowX = 0
        elif windowX > width:
            distance = round(windowX - width) / POP_FACTOR
            velX = (-velX * BOUNCE_FACTOR) + distance
            windowX = width

        if windowY > height:
            distance = round(windowY - height) / POP_FACTOR
            velY = (-velY * BOUNCE_FACTOR) + distance
            windowY = height
        elif windowY < 38:
            distance = round(windowY - 38) / POP_FACTOR
            velY = (-velY * BOUNCE_FACTOR) + distance
            windowY = 38

def Loop():
    global windowX, windowY, velX, velY

    if not mouseDown:
        windowX += velX
        windowY += velY
        CheckWindowStuff()
        root.geometry('+{}+{}'.format(int(windowX), int(windowY)))
        root.overrideredirect(True)
        velY += GRAVITY
        velX /= FRICTION

    root.after(8, Loop)

def animate_grow(i=1):
    if i <= 50:
        center_x = root.winfo_pointerx() + 50
        center_y = root.winfo_pointery() + 50
        root.geometry('+{}+{}'.format(int(center_x - i - 50), int(center_y - i - 50)))
        root.geometry(f"{i*2}x{i*2}")

        root.overrideredirect(True)
        
        root.after(10, animate_grow, i+1)
    else:
        global windowX, windowY
        windowX = root.winfo_x()
        windowY = root.winfo_y()
        Loop()

animate_grow()
root.mainloop()