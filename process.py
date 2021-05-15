import cv2 as cv
import os
import sys

import crop
import rotation


def validateArguments(infile, outfile):
    # verify that the input file exists
    if not os.path.exists(infile):
        print("input file '%s' does not exist" % (infile))
        return False

    # verify that the output file does not already exist
    if os.path.exists(outfile):
        print("'%s' already exists" % (outfile))
        return False

    # now that it's verified that the output file is not present, make sure that it can
    # be written to, so that the user doesn't waste time editing this file only to find
    # that it can't be written
    try:
        open(outfile, 'wb')
    except:
        print("can't write to output file '%s'" % (outfile))
        return False
    # don't leave the test file around
    os.unlink(outfile)

    return True


# This function processes a circle if the circle parm is True;
# else, process a rectangle
def processImage(circle=True):
    if len(sys.argv) < 3:
        print('%s <input image filename> <output image filename.PNG>' % (sys.argv[0]))
        sys.exit(1)

    inputFilename = sys.argv[1]
    outputFilename = sys.argv[2]

    if not validateArguments(inputFilename, outputFilename):
        print('could not validate arguments')
        return

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
