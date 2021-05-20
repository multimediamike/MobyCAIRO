import cv2 as cv
from PIL import Image, ImageTk
import screeninfo
import sys
import tkinter as tk
import tkinter.font as font

import process

action = None

# event handlers
def doRectangle(arg=None):
    global action
    action = "rectangle"
    root.destroy()


def doCircle(arg=None):
    global action
    action = "circle"
    root.destroy()


def doEscape(arg):
    global action
    action = None
    root.destroy()


# process arguments
if len(sys.argv) < 3:
    print('%s <input image filename> <output image filename>' % (sys.argv[0]))
    sys.exit(1)

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

if not process.validateArguments(inputFilename, outputFilename):
    print('could not validate arguments')
    sys.exit(1)

# create the UI frame
root = tk.Tk()
root.title('MobyCAIRO - Select Editing Mode')
frame = tk.Frame(root)
frame.pack()
largeFont = font.Font(size=40)

# top button
button = tk.Button(frame,
                   text="Process (R)ectangle",
                   command=doRectangle)
button['font'] = largeFont
button.pack(side=tk.TOP)

# query the monitor dimension
screen = screeninfo.get_monitors()[0]
screenWidth = int(screen.width * 0.95)
screenHeight = int(screen.height * 0.70)

# use OpenCV to load the image
image = cv.imread(inputFilename)

# scale down the image and move the window to the right side of the screen
minDimension = min(screenWidth, screenHeight)
ratio = max(minDimension / image.shape[0], minDimension / image.shape[1])
windowWidth = int(image.shape[1] * ratio)
windowHeight = int(image.shape[0] * ratio)
root.geometry("+%d+20" % (screenWidth-windowWidth))
scaledImage = cv.resize(image, (windowWidth, windowHeight))
scaledImage = cv.cvtColor(scaledImage, cv.COLOR_BGR2RGB)

# put the image on a label
image = ImageTk.PhotoImage(Image.fromarray(scaledImage))
photoLabel = tk.Label(frame, image=image)
photoLabel.pack(side=tk.TOP)

# bottom button
button = tk.Button(frame, 
                   text="Process (C)ircle",
                   command=doCircle)
button['font'] = largeFont
button.pack(side=tk.BOTTOM)

# bind the keyboard handlers
root.bind('<Escape>', doEscape)
root.bind('<R>', doRectangle)
root.bind('<r>', doRectangle)
root.bind('<C>', doCircle)
root.bind('<c>', doCircle)

# run the main UI loop
root.mainloop()

# proceed to the editing action
if action == 'circle':
    process.processImage(circle=True)
elif action == 'rectangle':
    process.processImage(circle=False)
else:
    print('exiting with no editing action')
