import cv2 as cv
import numpy as np
import screeninfo

import key_codes as key


def assistedCircleCrop(image, houghAnalysisSize=400):
    windowName = "MobyCAIRO - Assisted Circle Crop"

    # create window
    screen = screeninfo.get_monitors()[0]
    screenWidth = int(screen.width * 0.95)
    screenHeight = int(screen.height * 0.90)
    cv.namedWindow(windowName)

    (primeRows, primeCols, _) = image.shape

    # create the display-ready image
    primeToDisplayScaler = max(primeRows / screenWidth, primeCols / screenHeight)
    windowWidth = int(primeCols / primeToDisplayScaler)
    windowHeight = int(primeRows / primeToDisplayScaler)
    scaledImage = cv.resize(image, (windowWidth, windowHeight))
    cv.moveWindow(windowName, screenWidth-windowWidth, 0)

    # set up an image for analysis
    primeToAnalyzerScaler = min(primeRows, primeCols) / houghAnalysisSize
    analyzerWidth = int(primeCols / primeToAnalyzerScaler)
    analyzerHeight = int(primeRows / primeToAnalyzerScaler)
    analyzerImage = cv.resize(image, (analyzerWidth, analyzerHeight))
    (_, analyzerImage) = cv.threshold(analyzerImage, 60, 255, cv.THRESH_BINARY)
    analyzerImageGray = cv.cvtColor(analyzerImage, cv.COLOR_BGR2GRAY)
    minRadius = 0

    # find the circles
    print('searching the image for circles...')
    circles = cv.HoughCircles(analyzerImageGray, cv.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=minRadius, maxRadius=0)
    displayToAnalyzerScaler = 1.0 * primeToAnalyzerScaler / primeToDisplayScaler

    print("""=====================
Circle cropping interface:
  PgUp:  Select previous candidate circle
  PgDn:  Select next candidate circle
  W:     Increase radius by 1 pixel
  S:     Decrease radius by 1 pixel
  Left:  Move center point left 1 pixel
  Up:    Move center point up 1 pixel
  Right: Move center point right 1 pixel
  Down:  Move center point down 1 pixel
  Enter: Finalize crop and save image
  Esc:   Quit (without proceeding further)
""")

    index = 0
    # input loop
    while True:
        (centerX, centerY, radius) = circles[0][index]
        centerX = int(centerX * displayToAnalyzerScaler)
        centerY = int(centerY * displayToAnalyzerScaler)
        radius = int(radius * displayToAnalyzerScaler)
        displayImage = scaledImage.copy()
        cv.circle(displayImage, (centerX, centerY), radius, (0, 0, 255), 2)

        # show the update
        cv.imshow(windowName, displayImage)
        print('\r', end='')
        print('circle # %d/%d @ (%d, %d), r = %d    ' % (index+1, len(circles[0]), centerX, centerY, radius), end='', flush=True)

        keyCode = key.translateKey(cv.waitKeyEx(0))
        
        circle = circles[0][index]
        if keyCode == key.ESC:
            break
        elif keyCode == key.ENTER:
            break

        elif keyCode == key.PGUP:
            # select previous circle
            if index > 0:
                index -= 1
        elif keyCode == key.PGDOWN:
            # select next circle
            if index < len(circles[0]):
                index += 1

        elif keyCode == 'W':
            # increase radius
            circle[2] += 1
        elif keyCode == 'S':
            # decrease radius
            circle[2] -= 1
        
        elif keyCode == key.LEFT_ARROW:
            # move centerpoint left
            circle[0] -= 1
        elif keyCode == key.RIGHT_ARROW:
            # move centerpoint right
            circle[0] += 1
        
        elif keyCode == key.DOWN_ARROW:
            # move centerpoint down
            circle[1] += 1
        elif keyCode == key.UP_ARROW:
            # move centerpoint up
            circle[1] -= 1

    cv.destroyWindow(windowName)
    print()

    if keyCode != key.ENTER:
        return None

    # create a new canvas with all white and 1 cell of padding beyond the radius
    centerX = int(centerX * primeToDisplayScaler)
    centerY = int(centerY * primeToDisplayScaler)
    radius = int(radius * primeToDisplayScaler)
    diameter = int(radius*2) + 1
    croppedImage = np.zeros((diameter, diameter, 3), np.uint8)
    cv.rectangle(croppedImage, (0, 0), (diameter, diameter), (255, 255, 255), thickness=-1)

    # copy over the circle
    print('performing final crop...')
    croppedImage[radius][0:radius*2] = image[centerY][centerX-radius:centerX+radius]
    for i in range(radius):
        dx = int(np.sqrt(np.square(radius) - np.square(i)))
        croppedImage[radius-i][radius-dx:radius+dx] = image[centerY-i][centerX-dx:centerX+dx]
        croppedImage[radius+i][radius-dx:radius+dx] = image[centerY+i][centerX-dx:centerX+dx]

    return croppedImage


def assistedRectangleCrop(image):
    windowName = "MobyCAIRO - Rectangle Crop"

    # create window
    screen = screeninfo.get_monitors()[0]
    screenWidth = int(screen.width * 0.95)
    screenHeight = int(screen.height * 0.90)
    cv.namedWindow(windowName)

    (primeRows, primeCols, _) = image.shape

    # create the display-ready image
    primeToDisplayScaler = max(primeRows / screenWidth, primeCols / screenHeight)
    windowWidth = int(primeCols / primeToDisplayScaler)
    windowHeight = int(primeRows / primeToDisplayScaler)
    scaledImage = cv.resize(image, (windowWidth, windowHeight))
    cv.moveWindow(windowName, screenWidth-windowWidth, 0)

    print('select a rectangular region to crop and press ENTER to save the cropped image')
    (topX, topY, rectWidth, rectHeight) = cv.selectROI(windowName, scaledImage)
    topX = int(topX * primeToDisplayScaler)
    topY = int(topY * primeToDisplayScaler)
    bottomX = int(topX + rectWidth * primeToDisplayScaler)
    bottomY = int(topY + rectHeight * primeToDisplayScaler)

    if rectWidth <= 0 or rectHeight <= 0:
        return None
    print('performing final crop...')
    croppedImage = np.zeros((bottomY-topY, bottomX-topX, 3), np.uint8)
    # copy each line
    for i in range(topY, bottomY):
        croppedImage[i-topY][:] = image[i][topX:bottomX]

    return croppedImage
