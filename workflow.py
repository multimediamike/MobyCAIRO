import sys

import cv2 as cv

KEY_ESC = 27
KEY_ENTER = 13
KEY_LEFT_ARROW = 0x250000
KEY_UP_ARROW = 0x260000
KEY_RIGHT_ARROW = 0x270000
KEY_DOWN_ARROW = 0x280000

windowName = 'Process Image'

# would be nice to detect these parameters somehow
maxWidth = 3700
maxHeight = 2000
monitorScaleFactor = 1.75
ANALYSIS_SIZE = 400


def plotCircle(img, circle, xRatio, yRatio, windowName):
    (centerX, centerY, radius) = circle
    centerX = int(centerX * xRatio)
    centerY = int(centerY * yRatio)
    radius = int(radius * min(xRatio, yRatio))
    imgDisplay = img.copy()
    cv.circle(imgDisplay, (centerX, centerY), int(radius), (0, 0, 255), 2)
    cv.imshow(windowName, imgDisplay)


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
    cv.imshow("windowName", analyzerImageGray)

    # find the circles
    before = cv.getTickCount()
    circles = cv.HoughCircles(analyzerImageGray, cv.HOUGH_GRADIENT, 1, 20, param1=50, param2=30, minRadius=minRadius, maxRadius=0)
    after = cv.getTickCount()

    xRatio = imgShow.shape[0] / analyzerImage.shape[0]
    yRatio = imgShow.shape[1] / analyzerImage.shape[1]

    index = 0
    plotCircle(imgShow, circles[0][index], xRatio, yRatio, windowName)

    # input loop
    while True:
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
        
        circle = circles[0][index]
        if len(circle) > 0:
            print("circle %d @ (%d, %d), radius %d" % (index, circle[0], circle[1], circle[2]))
            plotCircle(imgShow, circle, xRatio, yRatio, windowName)

    if key == KEY_ESC:
        cv.destroyAllWindows()
        sys.exit(0)

    # clean up
    cv.destroyAllWindows()