import tkinter as tk

import process

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

print("time to process the image: circle? %s" % (str(circle)))
process.processImage(circle=circle)