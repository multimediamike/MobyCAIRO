import cv2 as cv
import numpy as np
import os
import screeninfo
import sys

import key_codes as key
import rotation


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
  Enter: Finalize rotation
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
    # copy the center line from original image to cropped image
    copyLine(image[centerY][centerX-radius:centerX+radius], croppedImage[radius][:])
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
    rotatedImage = rotation.assistedImageRotation(imagePrime)
    if rotatedImage is None:
        print('exiting program without saving the image')
        sys.exit(0)

    # detect circle and perform the crop
    croppedImage = assistedCircleCrop(rotatedImage)
    if croppedImage is None:
        print('exiting program without saving the image')
        sys.exit(0)

    # save the image
    print('saving rotated and cropped image to "%s"...' % (outputFilename))
    cv.imwrite(outputFilename, croppedImage)
