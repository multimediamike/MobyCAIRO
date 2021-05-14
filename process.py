import cv2 as cv
import os
import sys

import crop
import rotation


# This function processes a circle if the circle parm is True;
# else, process a rectangle
def processImage(circle=True):
    if len(sys.argv) < 3:
        print('%s <input image filename> <output image filename.PNG>' % (sys.argv[0]))
        sys.exit(1)

    inputFilename = sys.argv[1]
    outputFilename = sys.argv[2]

    # verify that the output file does not already exist
    if os.path.exists(outputFilename):
        print("'%s' already exists" % (outputFilename))
        sys.exit(2)

    # now that it's verified that the output file is not present, make sure that it can
    # be written to, so that the user doesn't waste time editing this file only to find
    # that it can't be written
    try:
        open(outputFilename, 'wb')
    except:
        print("can't write to output file '%s'" % (outputFilename))
        sys.exit(3)
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

    # crop image
    if circle:
        croppedImage = crop.assistedCircleCrop(rotatedImage)
    else:
        croppedImage = crop.assistedRectangleCrop(rotatedImage)
    if croppedImage is None:
        print('exiting program without saving the image')
        sys.exit(0)

    # save the image
    print('saving rotated and cropped image to "%s"...' % (outputFilename))
    cv.imwrite(outputFilename, croppedImage)
