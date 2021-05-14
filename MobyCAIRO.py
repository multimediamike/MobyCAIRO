import sys
import tkinter as tk

import process

if len(sys.argv) < 3:
    print('%s <input image filename> <output image filename.PNG>' % (sys.argv[0]))
    sys.exit(1)

circle = False

def do_circle():
    global circle
    circle = True
    root.destroy()

def do_rectangle():
    global circle
    circle = False
    root.destroy()

root = tk.Tk()
frame = tk.Frame(root)
frame.pack()

button = tk.Button(frame, 
                   text="Circle", 
                   command=do_circle)
button.pack(side=tk.LEFT)
slogan = tk.Button(frame,
                   text="Rectangle",
                   command=do_rectangle)
slogan.pack(side=tk.LEFT)

tk.Button()

root.mainloop()

process.processImage(circle=circle)