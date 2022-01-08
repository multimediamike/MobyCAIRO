import ctypes
from tkinter.constants import W
import cv2 as cv
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog


class MobyCAIRO:

    TAB_LOAD = 0
    TAB_ROTATE = 1
    TAB_CROP = 2
    TAB_SAVE = 3

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
        

    def tabChanged(self, event):
        if self.tabControl.index("current") == self.TAB_CROP:
            # the first time this tab is presented, select the default radio button
            if self.rotateTabFirstTransition:
#                self.radioCropCircle.select()
                self.rotateTabFirstTransition = False

            # if the rotation angle changed, recompute candidate crops
            currentAngleText = self.angleList.get(self.currentAngleIndex)
            if self.currentRotationAngle != currentAngleText:
                currentAngle = float(currentAngleText[:-1])
                self.currentRotationAngle = currentAngleText

                # compute a rotated image per the current rotation angle
                (rows, cols, _) = self.imagePrime.shape
                M = cv.getRotationMatrix2D(((cols-1)/2.0, (rows-1)/2.0), currentAngle, 1)
                rotatedImage = cv.warpAffine(self.imagePrime, M, (cols, rows))

                # compute most likely crop candidates
                self.findCircles(rotatedImage)
                self.findRects(rotatedImage)

                # populate the candidate circle crop list box
                for i in range(len(self.circles)):
                    (centerX, centerY, radius) = self.circles[i]
                    self.circleCropList.insert(i, str('(%d, %d), %d' % (centerX, centerY, radius)))

                # populate the candidate rectangle crop box
                for i in range(len(self.rects)):
                    (minX, minY, maxX, maxY, _) = self.rects[i]
                    self.rectCropList.insert(i, str('(%d, %d) -> (%d, %d)' % (minX, minY, maxX, maxY)))

            self.drawImage()


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

        # automatically skip to the next tab
        self.tabControl.select(1)

        # select the first angle in the list box
        self.angleList.select_set(0)

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


    def listEvent(self, event):
        if self.tabControl.index("current") == self.TAB_ROTATE:
            self.currentAngleIndex = self.angleList.curselection()[0]
        elif self.tabControl.index("current") == self.TAB_CROP:
            if len(self.circleCropList.curselection()):
                self.currentCropIndex = self.circleCropList.curselection()[0]
            elif len(self.rectCropList.curselection()):
                # re-use the same variable for rects, but negative
                self.currentCropIndex = -(self.rectCropList.curselection()[0]+1)
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


    def selectCropMode(self, mode):
        print(mode)


    def drawCallback(self):
        self.drawImage()


    #############################################
    # Image functions

    def createAnalyzerImage(self):
        if self.lineAnalyzerImage:
            return
        # create an image for Hough line analysis; convert color -> grayscale
        self.lineAnalyzerImage = cv.cvtColor(self.imagePrime, cv.COLOR_BGR2GRAY)
        # blur the image
        self.lineAnalyzerImage = cv.GaussianBlur(self.lineAnalyzerImage, (7, 7), 0)


    def straightLineAnalysis(self):
        self.createAnalyzerImage()

        # adapting the pipeline described in this Stack Overflow answer:
        #  https://stackoverflow.com/a/45560545/475067
        lowThreshold = 50
        highThreshold = 150
        edges = cv.Canny(self.lineAnalyzerImage, lowThreshold, highThreshold)
        edgesImage = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
        self.edgesImage = cv.resize(edgesImage, (self.windowWidth, self.windowHeight))
        rho = 1
        theta = np.pi / 180
        threshold = 15
        minLineLength = 50
        maxLineGap = 20
        lines = cv.HoughLinesP(edges, rho, theta, threshold, np.array([]), minLineLength=minLineLength, maxLineGap=maxLineGap)

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


    # Find the circles in an image.
    # Parameters:
    #   image: the image to be analyzed
    #   houghAnalysisSize: the pixel size to resize the image down to before
    #   analysis
    # Upon exit, this populates self.circles with a list of (X Y R) tuples
    #   defining circles, sorted in descending order by radius
    def findCircles(self, image, houghAnalysisSize=400):
        # set up an image for analysis
        (primeRows, primeCols, _) = image.shape
        circleScaleFactor = min(primeRows, primeCols) / houghAnalysisSize
        analyzerWidth = int(primeCols / circleScaleFactor)
        analyzerHeight = int(primeRows / circleScaleFactor)
        analyzerImage = cv.resize(image, (analyzerWidth, analyzerHeight))
        (_, analyzerImage) = cv.threshold(analyzerImage, 60, 255, cv.THRESH_BINARY)
        analyzerImageGray = cv.cvtColor(analyzerImage, cv.COLOR_BGR2GRAY)

        # find the circles
        circlesPrime = cv.HoughCircles(analyzerImageGray, cv.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=0, maxRadius=int(houghAnalysisSize/2))

        # qualify the discovered circles: no circles that go outside the box
        circles = []
        for circle in circlesPrime[0]:
            (centerX, centerY, radius) = circle
            if centerX - radius > 0 and \
               centerY - radius > 0 and \
               centerX + radius < houghAnalysisSize and \
               centerY + radius < houghAnalysisSize:

               # scale the parameters before appending
               circle = (int(centerX * circleScaleFactor), int(centerY * circleScaleFactor), int(radius * circleScaleFactor))
               circles.append(circle)

        # sort descending by radius
        self.circles = sorted(circles, key=lambda x: x[2])
        self.circles.reverse()


    # Find the rectangles in an image.
    # Parameters:
    #   image: the image to be analyzed
    #   houghAnalysisSize: the pixel size to resize the image down to before
    #   analysis
    # Upon exit, this populates self.rectanges with a list of (X Y R) tuples
    #   defining circles, sorted in descending order by radius
    def findRects(self, image, houghAnalysisSize=600):
        # set up an image for analysis
        (primeRows, primeCols, _) = image.shape
        rectScaleFactor = min(primeRows, primeCols) / houghAnalysisSize
        analyzerWidth = int(primeCols / rectScaleFactor)
        analyzerHeight = int(primeRows / rectScaleFactor)
        print(analyzerWidth, analyzerHeight)

        # recipe from here: https://dev.to/simarpreetsingh019/detecting-geometrical-shapes-in-an-image-using-opencv-4g72
        analyzerImage = cv.resize(image, (analyzerWidth, analyzerHeight))
        analyzerImageGray = cv.cvtColor(analyzerImage, cv.COLOR_BGR2GRAY)
        _, analyzerImage = cv.threshold(analyzerImageGray, 240, 255, cv.CHAIN_APPROX_NONE)

        rects = []
        contours, _ = cv.findContours(analyzerImage, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
        for contour in contours:
            approx = cv.approxPolyDP(contour, 0.01 * cv.arcLength(contour, True), True)
            if len(approx) == 4:
                minX = minY = 99999999
                maxX = maxY = 0
                for point in approx:
                    minX = min(minX, point[0][0])
                    maxX = max(maxX, point[0][0])
                    minY = min(minY, point[0][1])
                    maxY = max(maxY, point[0][1])
                minX *= rectScaleFactor
                minY *= rectScaleFactor
                maxX *= rectScaleFactor
                maxY *= rectScaleFactor
                area = (maxX - minX) * (maxY - minY)
                rects.append((minX, minY, maxX, maxY, area))

            # sort descending by rectangle area
            self.rects = sorted(rects, key=lambda x: x[4])
            self.rects.reverse()


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

        # draw the lines computed from the Hough transform (only in rotate mode)
        if self.tabControl.index("current") == self.TAB_ROTATE and self.showLineAnalysisCheckboxValue.get():
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

        # draw the current crop candidate
        if self.tabControl.index("current") == self.TAB_CROP:
            if self.currentCropIndex >= 0:
                (centerX, centerY, radius) = self.circles[self.currentCropIndex]
                cv.circle(scaledImage, (int(centerX/scaler), int(centerY/scaler)), int(radius/scaler), (255, 0, 0), 2)
                cv.rectangle(scaledImage, (int((centerX-radius)/scaler), int((centerY-radius)/scaler)), 
                    (int((centerX+radius)/scaler), int((centerY+radius)/scaler)), (200, 0, 0), 2)
            else:
                index = (-self.currentCropIndex) - 1
                (minX, minY, maxX, maxY, _) = self.rects[index]
                cv.rectangle(scaledImage, (int(minX/scaler), int(minY/scaler)), (int(maxX/scaler), int(maxY/scaler)), (255, 0, 0), 2)


        # convert to a form that Tk can display
        image = ImageTk.PhotoImage(Image.fromarray(scaledImage))
        self.imageLabel.configure(image=image)
        self.imageLabel.image = image


    #############################################
    # GUI functions

    def initLoadTab(self):
        self.loadTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.loadTab, text=" Load ")

        ttk.Label(self.loadTab, text="Load image: ").pack(side=tk.TOP, expand=tk.NO, padx=5, pady=5)
        self.buttonLoadFile = ttk.Button(self.loadTab, text="Select image file...", command=self.buttonClickLoadImage).pack(side=tk.TOP, expand=tk.NO, padx=5, pady=5)


    def initRotateTab(self):
        self.rotateTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.rotateTab, text=" Rotate ")

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

        ttk.Label(self.rotateTab, text="Candidate Angles: ").grid(column=0, row=6, padx=3, pady=10, sticky='ne')
        self.angleList = tk.Listbox(self.rotateTab)
        self.angleList.grid(column=1, columnspan=4, row=6, padx=5, pady=5, sticky='w')
        self.angleList.bind('<<ListboxSelect>>', self.listEvent)


    def initCropTab(self):
        self.rotateTabFirstTransition = True
        self.cropTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.cropTab, text=" Crop ")

        selected = tk.StringVar()
        """
        self.radioCropCircle = tk.Radiobutton(self.cropTab, text='Crop Circle', value='circle', variable=selected, command=lambda: self.selectCropMode('circle'))
        self.radioCropCircle.grid(column=0, row=0, padx=3, pady=10, sticky='w')
        self.radioCropRect = tk.Radiobutton(self.cropTab, text='Crop Rectangle', value='rect', variable=selected, command=lambda: self.selectCropMode('rect'))
        self.radioCropRect.grid(column=1, row=0, padx=3, pady=10, sticky='w')
        """

        ttk.Label(self.cropTab, text="Candidate Circles: ").grid(column=0, row=0, padx=3, pady=10, sticky='ne')
        self.circleCropList = tk.Listbox(self.cropTab)
        self.circleCropList.grid(column=1, row=0, padx=5, pady=5, sticky='w')
        self.circleCropList.bind('<<ListboxSelect>>', self.listEvent)

        ttk.Label(self.cropTab, text="Candidate Rectangles: ").grid(column=0, row=1, padx=3, pady=10, sticky='ne')
        self.rectCropList = tk.Listbox(self.cropTab)
        self.rectCropList.grid(column=1, row=1, padx=5, pady=5, sticky='w')
        self.rectCropList.bind('<<ListboxSelect>>', self.listEvent)


    def initSaveTab(self):
        self.saveTab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.saveTab, text=" Save ")


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
        self.tabControl.bind("<<NotebookTabChanged>>", self.tabChanged)

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
        self.lineAnalyzerImage = None

        # related to automated rotation
        self.currentAngleIndex = 0
        self.currentCropIndex = 0
        self.lineList = {}
        self.lineListByLength = {}
        self.currentRotationAngle = "0.00°"

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