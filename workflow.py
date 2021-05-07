import sys

import cv2 as cv
import numpy as np

KEY_ENTER = 13
KEY_ESC = 27
KEY_SPACE = 32
KEY_LEFT_ARROW = 0x250000
KEY_UP_ARROW = 0x260000
KEY_RIGHT_ARROW = 0x270000
KEY_DOWN_ARROW = 0x280000

windowName = 'MobyFlow'

# would be nice to detect these parameters somehow
maxWidth = 3700
maxHeight = 2000
monitorScaleFactor = 1.75
ANALYSIS_SIZE = 400


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('%s <image file>' % (sys.argv[0]))
        sys.exit(0)

    # load image
    imgPrime = cv.imread(sys.argv[1])

    # create window and sort out dimensions
    window = cv.namedWindow(windowName)
    cv.moveWindow(windowName, 200, 20)
    minDimension = min(maxWidth, maxHeight)
    ratio = min(minDimension / imgPrime.shape[0], minDimension / imgPrime.shape[1])
    windowWidth = int(imgPrime.shape[1] * ratio / monitorScaleFactor)
    windowHeight = int(imgPrime.shape[0] * ratio / monitorScaleFactor)
    imgShow = cv.resize(imgPrime, (windowWidth, windowHeight))

    # set up an image for analysis
    analyzerRatio = min(ANALYSIS_SIZE / imgPrime.shape[0], ANALYSIS_SIZE / imgPrime.shape[1])
    analyzerWidth = int(imgPrime.shape[1] * analyzerRatio)
    analyzerHeight = int(imgPrime.shape[0] * analyzerRatio)
    analyzerImage = cv.resize(imgPrime, (analyzerWidth, analyzerHeight))
    (ret, analyzerImage) = cv.threshold(analyzerImage, 60, 255, cv.THRESH_BINARY)
    analyzerImageGray = cv.cvtColor(analyzerImage, cv.COLOR_BGR2GRAY)
    minRadius = int(ANALYSIS_SIZE/2 * 0.50)
    maxRadius = int(ANALYSIS_SIZE)

    # find the circles
    before = cv.getTickCount()
    circles = cv.HoughCircles(analyzerImageGray, cv.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=minRadius, maxRadius=0)
    after = cv.getTickCount()

    xRatio = imgShow.shape[0] / analyzerImage.shape[0]
    yRatio = imgShow.shape[1] / analyzerImage.shape[1]

    index = 0

    # input loop
    while True:
        (centerX, centerY, radius) = circles[0][index]
        centerX = int(centerX * xRatio)
        centerY = int(centerY * yRatio)
        radius = int(radius * min(xRatio, yRatio))
        imgDisplay = imgShow.copy()
        cv.circle(imgDisplay, (centerX, centerY), int(radius), (0, 0, 255), 2)
        cv.imshow(windowName, imgDisplay)

        key = cv.waitKeyEx(0)
        if 32 <= key < 128:
            key = chr(key).upper()
        
        circle = circles[0][index]
        if key == KEY_ESC:
            break
        elif key == KEY_ENTER:
            break

        elif key == 'A':
            # select previous circle
            if index > 0:
                index -= 1
        elif key == 'D':
            # select next circle
            if index < len(circles[0]):
                index += 1

        elif key == 'W':
            # increase radius
            circle[2] += 1
        elif key == 'S':
            # decrease radius
            circle[2] -= 1
        
        elif key == KEY_LEFT_ARROW:
            # move centerpoint left
            circle[0] -= 1
        elif key == KEY_RIGHT_ARROW:
            # move centerpoint right
            circle[0] += 1
        
        elif key == KEY_DOWN_ARROW:
            # move centerpoint down
            circle[1] += 1
        elif key == KEY_UP_ARROW:
            # move centerpoint up
            circle[1] -= 1

    if key == KEY_ESC:
        cv.destroyAllWindows()
        sys.exit(0)

    lineAnalyzerImg = cv.cvtColor(imgShow, cv.COLOR_BGR2GRAY)
    lineAnalyzerImg = cv.GaussianBlur(lineAnalyzerImg, (7, 7), 0)

    # using this Stack Overflow answer as a reference:
    #  https://stackoverflow.com/a/45560545/475067
    lowThreshold = 50
    highThreshold = 150
    edges = cv.Canny(lineAnalyzerImg, lowThreshold, highThreshold)
    edgeDisplay = cv.cvtColor(edges, cv.COLOR_GRAY2BGR)
    rho = 1
    theta = np.pi / 180
    threshold = 15
    minLineLength = 50
    maxLineGap = 20

    lines = cv.HoughLinesP(edges, rho, theta, threshold, np.array([]), minLineLength=minLineLength, maxLineGap=maxLineGap)
    print(len(lines))
    lineList = {}
    for line in lines[:20]:
        for (x1, y1, x2, y2) in line:
            dx = x2 - x1
            dy = y2 - y1
            theta = round(np.arctan(dy/dx) * 180/np.pi)
            if theta not in lineList:
                lineList[theta] = { 'lines': set(), 'total': 0.0 }
            lineList[theta]['lines'].add((x1, y1, x2, y2))
            lineList[theta]['total'] += np.sqrt(np.square(dx) + np.square(dy))
    
    lineListByLength = {}
    for angle in lineList.keys():
        lineItem = lineList[angle]
        lineListByLength[lineItem['total']] = { 'lines': lineItem['lines'], 'angle': angle }
    
    lengths = lineListByLength.keys()
    lengths = sorted(lengths)
    lengths.reverse()
    print(len(lengths), lengths)

    # input loop
    index = 0
    displayLines = False
    while True:
        if displayLines:
            imgDisplay = edgeDisplay.copy()
        else:
            imgDisplay = imgShow.copy()
        for line in lineListByLength[lengths[index]]['lines']:
            (x1, y1, x2, y2) = line
            cv.line(imgDisplay, (x1, y1), (x2, y2), (0, 0, 255), 5)
        (rows, cols, _) = imgDisplay.shape
        M = cv.getRotationMatrix2D(((cols-1)/2.0,(rows-1)/2.0),lineListByLength[lengths[index]]['angle'],1)
        imgDisplay = cv.warpAffine(imgDisplay, M, (cols, rows))
        cv.imshow(windowName, imgDisplay)

        key = cv.waitKeyEx(0)
        if 32 < key < 128:
            key = chr(key).upper()
        
        if key == KEY_ESC:
            break
        elif key == KEY_ENTER:
            break
        elif key == KEY_SPACE:
            displayLines = not displayLines

        elif key == 'W':
            # select previous line
            if index > 0:
                index -= 1
        elif key == 'S':
            # select next line
            if index < len(lengths)-1:
                index += 1

    # clean up
    cv.destroyAllWindows()