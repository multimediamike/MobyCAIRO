import ctypes
import cv2 as cv
import numpy as np
import os
import screeninfo
import sys

import key_codes as key


def assistedImageRotation(image):
    windowName = "MobyCAIRO - Assisted Image Rotation"

    # create window
    screen = screeninfo.get_monitors()[0]
    screenWidth = int(screen.width * 0.95)
    screenHeight = int(screen.height * 0.90)
    cv.namedWindow(windowName)

    # create the display-ready image
    minDimension = min(screenWidth, screenHeight)
    ratio = min(minDimension / image.shape[0], minDimension / image.shape[1])
    windowWidth = int(image.shape[1] * ratio)
    widthRatio = image.shape[0] / windowWidth
    windowHeight = int(image.shape[0] * ratio)
    heightRatio = image.shape[1] / windowHeight
    scaledImage = cv.resize(image, (windowWidth, windowHeight))
    cv.moveWindow(windowName, screenWidth-windowWidth, 0)
    print("scaled %dx%d -> %dx%d for display" % (image.shape[1], image.shape[0], windowWidth, windowHeight))

    # create an image for Hough line analysis
    #lineAnalyzerImage = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    lineAnalyzerImage = cv.cvtColor(scaledImage, cv.COLOR_BGR2GRAY)
    lineAnalyzerImage = cv.GaussianBlur(lineAnalyzerImage, (7, 7), 0)

    # adapting the pipeline described in this Stack Overflow answer:
    #  https://stackoverflow.com/a/45560545/475067
    lowThreshold = 50
    highThreshold = 150
    edges = cv.Canny(lineAnalyzerImage, lowThreshold, highThreshold)
    edgesImage = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
    edgesImage = cv.resize(edgesImage, (windowWidth, windowHeight))
    rho = 1
    theta = np.pi / 180
    threshold = 15
    minLineLength = 50
    maxLineGap = 20
    lines = cv.HoughLinesP(edges, rho, theta, threshold, np.array([]), minLineLength=minLineLength, maxLineGap=maxLineGap)
    print("found %d line segments using probabilistic Hough line transform" % (len(lines)))

    # organize the line segments into bins according to their angles
    lineList = {}
    for line in lines[:]:
        for (x1, y1, x2, y2) in line:
            dx = x2 - x1
            dy = y2 - y1
            theta = round(np.arctan(dy/dx) * 180/np.pi)
            if theta not in lineList:
                lineList[theta] = { 'lines': set(), 'total': 0.0 }
            lineList[theta]['lines'].add((x1, y1, x2, y2))
            lineList[theta]['total'] += np.sqrt(np.square(dx) + np.square(dy))

    # organize the line list according to the most distance represented per angle
    lineListByLength = {}
    for angle in lineList.keys():
        lineItem = lineList[angle]
        lineListByLength[lineItem['total']] = { 'lines': lineItem['lines'], 'angle': angle * 1.0 }
    lengths = lineListByLength.keys()
    lengths = sorted(lengths)
    lengths.reverse()
    print("sorted %d line segments into %d angles" % (len(lines), len(lengths)))

    print("""=====================
Rotation interface:
  PgUp:  Select previous candidate angle
  PgDn:  Select next candidate angle
  Tab:   Rotate 90 degrees
  Up:    Rotate counter-clockwise 1 degree
  Down:  Rotate clockwise 1 degree
  Left:  Rotate counter-clockwise 0.1 degree
  Right: Rotate clockwise 0.1 degree
  Space: Toggle line analyzer display
  Enter: Finalize rotation
  Esc:   Quit (without proceeding further)
""")

    index = 0
    displayLines = False

    # input loop
    while True:
        # choose which image to display: real image or the computed edges
        if displayLines:
            displayImage = edgesImage.copy()
        else:
            displayImage = scaledImage.copy()
        
        # draw the lines computed from the Hough transform
        for line in lineListByLength[lengths[index]]['lines']:
            (x1, y1, x2, y2) = line
            cv.line(displayImage, (x1, y1), (x2, y2), (0, 0, 255), 2)

        # rotate the image so that the angle of the computed lines is parallel to the horizontal
        (rows, cols, _) = displayImage.shape
        angle = lineListByLength[lengths[index]]['angle']
        M = cv.getRotationMatrix2D(((cols-1)/2.0, (rows-1)/2.0), angle, 1)
        displayImage = cv.warpAffine(displayImage, M, (cols, rows))

        # draw a light-colored grid
        if not displayLines:
            for x in range(1, windowWidth, 20):
                cv.line(displayImage, (x, 0), (x, windowHeight), (64, 64, 64), 1)
            for y in range(1, windowHeight, 20):
                cv.line(displayImage, (0, y), (windowWidth, y), (64, 64, 64), 1)

        # display the image
        cv.imshow(windowName, displayImage)
        print('\r', end='')
        print('rotation # %d/%d (%3.1f degrees)    ' % (index+1, len(lineListByLength), angle), end='', flush=True)

        keyCode = cv.waitKeyEx(0)
        if 32 < keyCode < 128:
            keyCode = chr(keyCode).upper()

        if keyCode == key.ESC:
            break
        elif keyCode == key.ENTER:
            break
        elif keyCode == key.SPACE:
            displayLines = not displayLines
        
        elif keyCode == key.PGUP:
            if index-1 >= 0:
                index -= 1
        elif keyCode == key.PGDOWN:
            if index+1 < len(lengths):
                index += 1

        elif keyCode == key.LEFT_ARROW:
            lineListByLength[lengths[index]]['angle'] += 0.1
        elif keyCode == key.RIGHT_ARROW:
            lineListByLength[lengths[index]]['angle'] -= 0.1

        elif keyCode == key.UP_ARROW:
            lineListByLength[lengths[index]]['angle'] += 1.0
        elif keyCode == key.DOWN_ARROW:
            lineListByLength[lengths[index]]['angle'] -= 1.0

        elif keyCode == key.TAB:
            lineListByLength[lengths[index]]['angle'] += 90.0

    cv.destroyWindow(windowName)
    print()

    if keyCode == key.ESC:
        return None
    elif keyCode == key.ENTER:
        # perform final rotation on the original image
        (rows, cols, _) = image.shape
        M = cv.getRotationMatrix2D(((cols-1)/2.0,(rows-1)/2.0),lineListByLength[lengths[index]]['angle'],1)
        image = cv.warpAffine(image, M, (cols, rows))
        return image
    else:
        return None


def assistedCircleCrop(image, houghAnalysisSize=400):
    windowName = "MobyCAIRO - Assisted Circle Crop"

    # create window
    screen = screeninfo.get_monitors()[0]
    screenWidth = int(screen.width * 0.95)
    screenHeight = int(screen.height * 0.90)
    cv.namedWindow(windowName)

    # create the display-ready image
    minDimension = min(screenWidth, screenHeight)
    print(screenWidth, screenHeight, minDimension)
    ratio = min(minDimension / image.shape[0], minDimension / image.shape[1])
    windowWidth = int(image.shape[1] * ratio)
    widthRatio = image.shape[0] / windowWidth
    windowHeight = int(image.shape[0] * ratio)
    heightRatio = image.shape[1] / windowHeight
    scaledImage = cv.resize(image, (windowWidth, windowHeight))
    cv.moveWindow(windowName, screenWidth-windowWidth, 0)
    print("ratio = %d, widthRatio = %d, heightRatio = %d" % (ratio, widthRatio, heightRatio))
    print("scaled %dx%d -> %dx%d for display" % (image.shape[1], image.shape[0], windowWidth, windowHeight))

    # set up an image for analysis
    analyzerRatio = min(houghAnalysisSize / image.shape[0], houghAnalysisSize / image.shape[1])
    analyzerWidth = int(image.shape[1] * analyzerRatio)
    analyzerHeight = int(image.shape[0] * analyzerRatio)
    analyzerImage = cv.resize(image, (analyzerWidth, analyzerHeight))
    (_, analyzerImage) = cv.threshold(analyzerImage, 60, 255, cv.THRESH_BINARY)
    analyzerImageGray = cv.cvtColor(analyzerImage, cv.COLOR_BGR2GRAY)
    minRadius = 0

    # find the circles
    print('searching the image for circles...')
    circles = cv.HoughCircles(analyzerImageGray, cv.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=minRadius, maxRadius=0)

    xRatio = scaledImage.shape[1] / analyzerImage.shape[1]
    yRatio = scaledImage.shape[0] / analyzerImage.shape[0]

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
  Enter: Finalize rotation
  Esc:   Quit (without proceeding further)
""")

    index = 0
    print(xRatio, yRatio)
    # input loop
    while True:
        (centerX, centerY, radius) = circles[0][index]
        centerX = int(centerX * xRatio)
        centerY = int(centerY * yRatio)
        radius = int(radius * min(xRatio, yRatio))
        displayImage = scaledImage.copy()
        cv.circle(displayImage, (centerX, centerY), int(radius), (0, 0, 255), 2)

        # show the update
        cv.imshow(windowName, displayImage)
        print('\r', end='')
        print('circle # %d/%d @ (%d, %d), r = %d    ' % (index+1, len(circles[0]), centerX, centerY, radius), end='', flush=True)

        keyCode = cv.waitKeyEx(0)
        if 32 <= keyCode < 128:
            keyCode = chr(keyCode).upper()
        
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

    print(radius, radius*widthRatio)

    if key != key.ENTER:
        return None

    # create a new canvas with all white and 1 cell of padding beyond the radius
    centerX = int(centerX * widthRatio)
    centerY = int(centerY * widthRatio)
    radius = int(radius * widthRatio)
    diameter = int(radius*2) + 1
    print('scaled radius = %d, radius = %d, diameter = %d' % (radius, radius*widthRatio, diameter))
    croppedImage = np.zeros((diameter, diameter, 3), np.uint8)
    cv.rectangle(croppedImage, (0, 0), (diameter, diameter), (255, 255, 255), thickness=-1)

    # copy over the circle
    # copy the center line from original image to cropped image
    copyLine(image[centerY][centerX-radius:centerX+radius], croppedImage[radius+1][:])
    # copy each line
    for i in range(radius):
        dx = int(np.sqrt(np.square(radius) - np.square(i)))
        copyLine(image[centerY-i][centerX-dx:centerX+dx], croppedImage[radius-i][radius-dx:radius+dx])
        copyLine(image[centerY+i][centerX-dx:centerX+dx], croppedImage[radius+i][radius-dx:radius+dx])

    return croppedImage


def copyLine(source, dest):
    i = 0
    for pixel in source:
        dest[i] = pixel
        i += 1


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('%s <input image filename> <output image filename.PNG>' % (sys.argv[0]))
        sys.exit(0)

    inputFilename = sys.argv[1]
    outputFilename = sys.argv[2]

    # verify that the output file does not already exist
    if os.path.exists(outputFilename):
        print("'%s' already exists" % (outputFilename))
        sys.exit(1)

    # now that it's verified that the output file is not present, make sure that it can
    # be written to, so that the user doesn't waste time editing this file only to find
    # that it can't be written
    try:
        open(outputFilename, 'wb')
    except:
        print("can't write to output file '%s'" % (outputFilename))
        sys.exit(1)
    # don't leave the test file around
    os.unlink(outputFilename)

    # load the image
    imagePrime = cv.imread(inputFilename)
    print("read image '%s', %dx%d" % (inputFilename, imagePrime.shape[1], imagePrime.shape[0]))

    # rotate image
    rotatedImage = assistedImageRotation(imagePrime)
    if rotatedImage is None:
        print('exiting program without saving the image')
        sys.exit(0)

    # detect circle and perform the crop
    croppedImage = assistedCircleCrop(rotatedImage)
    if croppedImage is None:
        print('exiting program without saving the image')
        sys.exit(0)

    # save the image
    cv.imwrite(outputFilename, croppedImage)
