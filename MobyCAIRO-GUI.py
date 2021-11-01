import ctypes
from tkinter.constants import W
import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog


class MobyCAIRO:

    filetypes = (
        ('Image files', '*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.bmp'),
        ('All files', '*.*')
    )

    logoFilename = "MobyCAIRO.png"


    #############################################
    # Event handlers

    def windowIsReady(self, event):
        self.windowWidth = self.imageLabel.winfo_width()
        self.windowHeight = self.imageLabel.winfo_height()
        self.windowAspect = self.windowWidth / self.windowHeight
        

    def buttonClickLoadImage(self):
        self.imageFilename = tkinter.filedialog.askopenfilename(
            title='Open image to process',
            filetypes=self.filetypes,
            parent=self.parent
        )
        self.imagePrime = cv.imread(self.imageFilename)
        self.imagePrime = cv.cvtColor(self.imagePrime, cv.COLOR_BGR2RGB)
        self.imagePrimeWidth = self.imagePrime.shape[1]
        self.imagePrimeHeight = self.imagePrime.shape[0]
        self.imagePrimeAspect = 1.0 * self.imagePrimeWidth / self.imagePrimeHeight

        # perform straight line analysis to find possible rotation candidate angles
        self.straightLineAnalysis()
        # populate the candidate angle list box
        for i in range(len(self.lengths)):
            self.angleList.insert(i, str('%0.2f' % self.lineListByLength[self.lengths[i]]['angle']) + '°')
        self.drawImage()


    def imageLabelMouseDown(self, event):
        self.movingImage=True
        self.parent.config(cursor='fleur')


    def imageLabelMouseMove(self, event):
        if not self.movingImage:
            return


    def imageLabelMouseUp(self, event):
        self.movingImage=False
        self.parent.config(cursor='arrow')


    def angleListEvent(self, event):
        self.currentAngleIndex = self.angleList.curselection()[0]
        self.drawImage()

    
    def rotateImage(self, angleAdjustment):
        angle = self.lineListByLength[self.lengths[self.currentAngleIndex]]['angle'] * 1.0
        angle += float(angleAdjustment)
        if angle > 180:
            angle -= 360
        self.lineListByLength[self.lengths[self.currentAngleIndex]]['angle'] = angle
        self.angleList.delete(self.currentAngleIndex)
        self.angleList.insert(self.currentAngleIndex, str('%0.2f' % angle) + '°')
        self.drawImage()


    def drawCallback(self):
        self.drawImage()


    #############################################
    # Image functions

    def straightLineAnalysis(self):
        # create an image for Hough line analysis; convert color -> grayscale
        lineAnalyzerImage = cv.cvtColor(self.imagePrime, cv.COLOR_BGR2GRAY)
        # blur the image
        lineAnalyzerImage = cv.GaussianBlur(lineAnalyzerImage, (7, 7), 0)

        # adapting the pipeline described in this Stack Overflow answer:
        #  https://stackoverflow.com/a/45560545/475067
        lowThreshold = 50
        highThreshold = 150
        edges = cv.Canny(lineAnalyzerImage, lowThreshold, highThreshold)
        edgesImage = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
        self.edgesImage = cv.resize(edgesImage, (self.windowWidth, self.windowHeight))
        rho = 1
        theta = np.pi / 180
        threshold = 15
        minLineLength = 50
        maxLineGap = 20
        lines = cv.HoughLinesP(edges, rho, theta, threshold, np.array([]), minLineLength=minLineLength, maxLineGap=maxLineGap)
        print("found %d line segments using probabilistic Hough line transform" % (len(lines)))

        # organize the line segments into bins according to their angles
        for line in lines[:]:
            for (x1, y1, x2, y2) in line:
                dx = x2 - x1
                dy = y2 - y1
                # special case for vertical line
                if dx == 0:
                    theta = 90
                else:
                    theta = round(np.arctan(dy/dx) * 180/np.pi)
                if theta not in self.lineList:
                    self.lineList[theta] = { 'lines': set(), 'total': 0.0 }
                self.lineList[theta]['lines'].add((x1, y1, x2, y2))
                # accumulate line length
                self.lineList[theta]['total'] += np.sqrt(np.square(dx) + np.square(dy))

        # organize the line list according to the most distance represented per angle
        for angle in self.lineList.keys():
            lineItem = self.lineList[angle]
            self.lineListByLength[lineItem['total']] = { 'lines': lineItem['lines'], 'angle': angle * 1.0 }
        lengths = self.lineListByLength.keys()
        self.lengths = sorted(lengths)
        self.lengths.reverse()
        self.angleList.select_set(0)
        self.angleList.event_generate("<<ListboxSelect>>")


    def drawImage(self):
        if self.imagePrimeAspect > self.windowAspect:
            scaler = self.imagePrimeWidth / self.windowWidth
        else:
            scaler = self.imagePrimeHeight / self.windowHeight
        scaledWidth = int(self.imagePrimeWidth / scaler)
        scaledHeight = int(self.imagePrimeHeight / scaler)
        if self.showComputedEdgesCheckboxValue.get():
            scaledImage = cv.resize(self.edgesImage, (scaledWidth, scaledHeight))
        else:
            scaledImage = cv.resize(self.imagePrime, (scaledWidth, scaledHeight))

        # draw the lines computed from the Hough transform
        if self.showLineAnalysisCheckboxValue.get():
            for line in self.lineListByLength[self.lengths[self.currentAngleIndex]]['lines']:
                (x1, y1, x2, y2) = line
                x1 = int(x1 / scaler)
                y1 = int(y1 / scaler)
                x2 = int(x2 / scaler)
                y2 = int(y2 / scaler)
                cv.line(scaledImage, (x1, y1), (x2, y2), (255, 0, 0), 1)

        # rotate the image so that the angle of the computed lines is parallel to the horizontal
        (rows, cols, _) = scaledImage.shape
        angle = self.lineListByLength[self.lengths[self.currentAngleIndex]]['angle']
        M = cv.getRotationMatrix2D(((cols-1)/2.0, (rows-1)/2.0), angle, 1)
        scaledImage = cv.warpAffine(scaledImage, M, (cols, rows))

        # draw a light-colored grid
        if self.showGridLinesCheckboxValue.get():
            for x in range(1, scaledWidth, 20):
                cv.line(scaledImage, (x, 0), (x, scaledHeight), (64, 64, 64), 1)
            for y in range(1, scaledHeight, 20):
                cv.line(scaledImage, (0, y), (scaledWidth, y), (64, 64, 64), 1)

        # convert to a form that Tk can display
        image = ImageTk.PhotoImage(Image.fromarray(scaledImage))
        self.imageLabel.configure(image=image)
        self.imageLabel.image = image


    #############################################
    # GUI functions

    def initLoadTab(self):
        self.loadTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.loadTab, text="Load")

        ttk.Label(self.loadTab, text="Load image: ").pack(side=tk.TOP, expand=tk.NO, padx=5, pady=5)
        self.buttonLoadFile = ttk.Button(self.loadTab, text="Select image file...", command=self.buttonClickLoadImage).pack(side=tk.TOP, expand=tk.NO, padx=5, pady=5)


    def initRotateTab(self):
        self.rotateTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.rotateTab, text="Rotate")

        # work on the zoom feature a bit later
        #ttk.Label(self.rotateTab, text="Zoom: ").grid(column=0, row=0, padx=3, pady=10, sticky='e')
        #self.buttonZoomIn = ttk.Button(self.rotateTab, text="In", command=None).grid(column=1, row=0, padx=3, pady=10)
        #self.buttonZoomOut = ttk.Button(self.rotateTab, text="Out", command=None).grid(column=2, row=0, padx=3, pady=10)

        ttk.Label(self.rotateTab, text="Counter clockwise: ").grid(column=0, row=1, padx=3, pady=10, sticky='e')
        self.buttonCounter90  = ttk.Button(self.rotateTab, text="90",   command=lambda: self.rotateImage(90)).grid( column=1, row=1, padx=3, pady=10)
        self.buttonCounter1   = ttk.Button(self.rotateTab, text="1",    command=lambda: self.rotateImage(1)).grid(  column=2, row=1, padx=3, pady=10)
        self.buttonCounter01  = ttk.Button(self.rotateTab, text="0.1",  command=lambda: self.rotateImage(.1)).grid( column=3, row=1, padx=3, pady=10)
        self.buttonCounter001 = ttk.Button(self.rotateTab, text="0.01", command=lambda: self.rotateImage(.01)).grid(column=4, row=1, padx=3, pady=10)

        ttk.Label(self.rotateTab, text="Clockwise: ").grid(column=0, row=2, padx=3, pady=10, sticky='e')
        self.buttonClock90  = ttk.Button(self.rotateTab, text="90",   command=lambda: self.rotateImage(-90)).grid( column=1, row=2, padx=3, pady=10)
        self.buttonClock1   = ttk.Button(self.rotateTab, text="1",    command=lambda: self.rotateImage(-1)).grid(  column=2, row=2, padx=3, pady=10)
        self.buttonClock01  = ttk.Button(self.rotateTab, text="0.1",  command=lambda: self.rotateImage(-.1)).grid( column=3, row=2, padx=3, pady=10)
        self.buttonClock001 = ttk.Button(self.rotateTab, text="0.01", command=lambda: self.rotateImage(-.01)).grid(column=4, row=2, padx=3, pady=10)

        ttk.Label(self.rotateTab, text="Clockwise: ").grid(column=0, row=2, padx=3, pady=10, sticky='e')
        self.showGridLinesCheckboxValue = tk.IntVar(value=1)
        self.showGridLinesCheckbox = ttk.Checkbutton(self.rotateTab, text="Show grid lines", variable=self.showGridLinesCheckboxValue, command=self.drawImage).grid(column=0, row=3, padx=3, pady=10, sticky='w')
        self.showLineAnalysisCheckboxValue = tk.IntVar(value=1)
        self.showLineAnalysisCheckbox = ttk.Checkbutton(self.rotateTab, text="Show line analysis", variable=self.showLineAnalysisCheckboxValue, command=self.drawImage).grid(column=0, row=4, padx=3, pady=10, sticky='w')
        self.showComputedEdgesCheckboxValue = tk.IntVar(value=0)
        self.showComputedEdgesCheckbox = ttk.Checkbutton(self.rotateTab, text="Show computed edges", variable=self.showComputedEdgesCheckboxValue, command=self.drawImage).grid(column=0, row=5, padx=3, pady=10, sticky='w')

        ttk.Label(self.rotateTab, text="Candidate Angles: ").grid(column=0, row=6, padx=3, pady=10, sticky='e')
        self.angleList = tk.Listbox(self.rotateTab)
        self.angleList.grid(column=1, columnspan=4, row=6, padx=5, pady=5, sticky='w')
        self.angleList.bind('<<ListboxSelect>>', self.angleListEvent)


    def initCropTab(self):
        self.cropTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.cropTab, text="Crop")


    def initSaveTab(self):
        self.saveTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.saveTab, text="Save")


    def initGUI(self):
        # set up window
        self.parent.title('MobyCAIRO')
        self.parent.state('zoomed')
        self.mainContainer = tk.Frame(self.parent)
        self.mainContainer.pack(expand=tk.YES, fill=tk.BOTH)

        # set up the controller frame
        self.controlFrame = tk.Frame(self.mainContainer)
        self.controlFrame.pack(side=tk.LEFT, expand=tk.NO, padx=5, pady=5, ipadx=5, ipady=5)

        # load the logo
        self.logoImage = ImageTk.PhotoImage(Image.open(self.logoFilename))
        self.logoLabel = tk.Label(self.controlFrame, image=self.logoImage)
        self.logoLabel.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)

        # make a tab control
        self.tabControl = ttk.Notebook(self.controlFrame)

        # initialize the tabs
        self.initLoadTab()
        self.initRotateTab()
        self.initCropTab()
        self.initSaveTab()
        self.tabControl.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)

        # set up the picture frame
        self.pictureFrame = tk.Frame(self.mainContainer)
        self.pictureFrame.pack(side=tk.RIGHT, expand=tk.YES)

        # create a giant blank image to plot on the image label in order
        # to push the image out to the boundaries; obtain the actual
        # resolution of the image window when the Map event is received
        blankImage = np.zeros((5000, 5000, 3), np.uint8)
        image = ImageTk.PhotoImage(Image.fromarray(blankImage))
        self.imageLabel = tk.Label(self.pictureFrame, image=image)
        self.imageLabel.pack(side=tk.RIGHT, expand=tk.YES)
        
        self.imageLabel.bind('<ButtonPress-1>', self.imageLabelMouseDown)
        self.imageLabel.bind('<Motion>', self.imageLabelMouseMove)
        self.imageLabel.bind('<ButtonRelease-1>', self.imageLabelMouseUp)
        self.imageLabel.bind('<Map>', self.windowIsReady)


    def __init__(self, parent):
        self.parent = parent
        self.movingImage = False

        # related to automated rotation
        self.currentAngleIndex = 0
        self.lineList = {}
        self.lineListByLength = {}

        # figure out scaling
        self.scaleFactor = 1.0
        if hasattr(ctypes, 'windll'):
            self.scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
        self.parent.tk.call('tk', 'scaling', self.scaleFactor)

        # initialize GUI elements and event callbacks
        self.initGUI()


if __name__ == '__main__':
    root = tk.Tk()
    app = MobyCAIRO(root)
    root.mainloop()