# MobyCAIRO

MobyCAIRO stands for **C**omputer-**A**ssisted **I**mage **RO**tation. It is designed to assist a user in the common, tedious tasks of rotating and cropping images.

The 'Moby' portion of the name is due to its original purpose being to help alleviate the tedium of straightening cover art scans for submission to the [MobyGames online video game database](https://www.mobygames.com/).

## Introduction

The tool is a run from the command line with an input image filename and an output image filename. It first presents the image with a grid overlay and allows the user to cycle through the most likely rotation angles in order to straighten the image. When the user is satisfied, that the image is straight, the tool then assists to find the best circle or rectangle cropping region. Then it saves the final edit back to the PNG output file specified on the command line.

## Demonstration By Screenshots

When run the UI will first show the image and ask whether to edit the image as a rectangle or a circle. This choice changes the cropping interface that is used in the cropping phase (automatically detecting a circle and allowing fine adjustments, or a simple rectangular image select). Click on 1 of the 2 buttons, or press 'c' or 'r' if you are more keyboard-oriented:

![MobyCAIRO Editing Mode Selection](https://multimedia.cx/pictures/MobyCAIRO/MobyCAIRO-select-editing-mode.jpg)

Next, MobyCAIRO finds the straight lines in the image, groups them by angles, and shows the most likely rotation while allowing the user to select among candidate angles and make fine adjustments. Further, the tool overlays a light grid which helps to visually verify straightness:

![MobyCAIRO Assisted Rotation](https://multimedia.cx/pictures/MobyCAIRO/MobyCAIRO-circle-rotation.jpg)

In this mode, the tool also allows toggling to see the edges that are used to determine how straight lines were discovered in the image:

![MobyCAIRO Show Detected Lines](https://multimedia.cx/pictures/MobyCAIRO/MobyCAIRO-show-lines.png)

When the image as been satisfactorily straightened, MobyCAIRO presents the user with an interface to crop the image. For a rectangular crop, the tool provides a simple mouse-driven interface. For a circle, however, MobyCAIRO assists the user by attempting to find the most likely circle. Similar to the assisted rotation, the tool allows the user to switch between likely candidate circles and also make fine adjustments.

![MobyCAIRO Assisted Circle Crop](https://multimedia.cx/pictures/MobyCAIRO/MobyCAIRO-assisted-circle-crop.jpg)

When the crop regions are set, the user can exit the program to save the final edited image.

## Supported Input Image Formats

MobyCAIRO uses the [OpenCV](https://opencv.org/) computer vision library. MobyCAIRO can read any format that the underlying OpenCV library supports, which includes:

* Windows bitmaps - \*.bmp, \*.dib
* JPEG files - \*.jpeg, \*.jpg, *.jpe 
* JPEG 2000 files - \*.jp2
* Portable Network Graphics - \*.png
* WebP - \*.webp
* Portable image format - \*.pbm, \*.pgm, \*.ppm \*.pxm, \*.pnm
* TIFF files - \*.tiff, \*.tif

*(source: https://docs.opencv.org/master/d4/da8/group__imgcodecs.html)*

Note that there are a few caveats to the above support, as well as some more supported format. See [the OpenCV documentation](https://docs.opencv.org/master/d4/da8/group__imgcodecs.html) for specifics.

## Installation From Source

* Clone this repository
* Create a virtual environment for Python 3: `virtualenv -p python3 venv`
* Activate the virtual environment.
  * On Windows: `venv\Scripts\activate.bat`
  * On Linux: `source venv/bin/activate`
* Install the required libraries: `pip install -r requirements.txt`

## Running The Tool

There are 2 separate tools: one for processing circles (e.g., scans of CD-ROMs), and one for processing rectangles (e.g., scans of boxes or jewel cases artwork).

* `python process-circle.py <input-scan.ext> <output.png>`
* `python process-rectangle.py <input-scan.ext> <output.png>`

After launching, MobyCAIRO will create a window on the right side of the screen while presenting a keyboard-based user interface on the terminal.

```
Rotation interface:
  PgUp:  Select previous candidate angle
  PgDn:  Select next candidate angle
  `:     Rotate 90 degrees
  Up:    Rotate counter-clockwise 1 degree
  Down:  Rotate clockwise 1 degree
  Left:  Rotate counter-clockwise 0.1 degree
  Right: Rotate clockwise 0.1 degree
  Space: Toggle line analyzer display
  Enter: Finalize rotation
  Esc:   Quit (without proceeding further)
```

```
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
```

For cropping a rectangle, MobyCAIRO uses OpenCV's mouse-driven interface for selecting the crop region.
