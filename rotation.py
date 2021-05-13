import cv2 as cv
import numpy as np
import screeninfo

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
    windowHeight = int(image.shape[0] * ratio)
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


