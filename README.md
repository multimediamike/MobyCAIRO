![MobyCAIRO Logo](/MobyCAIRO.png?raw=true "MobyCAIRO Logo")

MobyCAIRO stands for **C**omputer-**A**ssisted **I**mage **RO**tation. It is designed to assist a user in the common, tedious tasks of rotating and cropping images.

The 'Moby' portion of the name is due to its original purpose being to help alleviate the tedium of straightening cover art scans for submission to the [MobyGames online video game database](https://www.mobygames.com/).

## Demonstration By Screenshots

When run, the MobyCAIRO GUI will prompt the user to load an image for processing. After loading, GUI transitions to the Rotate tab. This tab attempts to automatically detect the most likely rotation angle that will make the image straight, correcting for skew introduced in scanning the image. This is computed by detecting groups of straight lines in the image. The user can select from a number of angles and then make fine adjustments in 1, 0.1, or 0.01 degree increments:

![Rotation interface](https://multimedia.cx/pictures/MobyCAIRO/mobycairo-gui-rotation.jpg)

The rotation tab also allows toggling the image view to reveal the edges that MobyCAIRO used to find the straight ones.

![Rotation interface -- edge view](https://multimedia.cx/pictures/MobyCAIRO/mobycairo-gui-rotation-edges.jpg)

After straightening the image using the Rotate tab, move to the Crop tab. By default, MobyCAIRO will detect circles as crop candidates, and allow the user to choose among them using a list box where the circles are listed in descending order by size. Keyboard controls allow fine controls to adjust the circle:

![Circular cropping interface](https://multimedia.cx/pictures/MobyCAIRO/mobycairo-gui-circle-crop.jpg)

For selecting a rectangular region to crop, simply use the mouse to select the region:

![Rectangular cropping interface](https://multimedia.cx/pictures/MobyCAIRO/mobycairo-gui-rectangle-crop.jpg)

Once the image is rotated and cropped, move on to the Save tab which prompts the user for a filename for saving the image.

![Save interface](https://multimedia.cx/pictures/MobyCAIRO/mobycairo-gui-final-save.jpg)

*See the final straightenend and cropped scans for [this CD-ROM and related jewel case artifacts at the Internet Archive](https://archive.org/details/cdrom-WhiteWolfSoftwareSeries29).*

## Downloading MobyCAIRO

MobyCAIRO is a tool that runs on a user's local machine (as opposed to running in a web browser). There are 2 options for getting MobyCAIRO:

1. Download the binary release: [The releases page](https://github.com/multimediamike/MobyCAIRO/releases) provides pre-built standalone binaries (presently only available for Windows)
2. Download the Python source code, install the dependencies, and run the tool (should work on Windows, Linux, and Mac OS X)

### Installation From Source

* Clone this repository
* Create a virtual environment for Python 3: `virtualenv -p python3 venv`
* Activate the virtual environment.
  * On Windows: `venv\Scripts\activate.bat`
  * On Linux/Mac OS X: `source venv/bin/activate`
* Install the required libraries: `pip install -r requirements.txt`

## Running The Tool

In order to run the tool on Windows, the easiest approach is to download the release EXE and double-click it from Windows Explorer.

On other platforms, establish and activate the Python environment as described in the previous step, and then execute:  `python MobyCAIRO.py`

## Technical Details

### Supported Input Image Formats

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

### Technologies and Algorithms

These are the technologies used to build this tool:

* [Python 3](https://www.python.org/): The computer language used to code the tool
* [Tkinter](https://docs.python.org/3/library/tkinter.html): The cross-platform GUI library
* [OpenCV](https://opencv.org/): Open source computer vision library use for image manipulation, feature detection
  - [Hough transform](https://en.wikipedia.org/wiki/Hough_transform) for finding straight lines and circles
  - [Canny edge detector](https://en.wikipedia.org/wiki/Canny_edge_detector) for highlighting the edges of an image

You can read more about the program's development from [this blog post by the author](https://multimedia.cx/eggs/developing-mobycairo/).

Thanks to [The e-Reader Preservation Project](https://hitsave.org/blog/nintendo-e-reader-preservation-the-ren-e-ssance/) for the cool MobyCAIRO logo.
