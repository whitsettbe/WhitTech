"""
TITLE:          Image Previewer
                                                                                |
DESCRIPTION:    Manages popup image previewer for the user. Detects images
                    stored in `preview` directory (subfolder of the installation
                    directory) and displays them in matplotlib. Images are
                    deleted from the preview folder after they are loaded.
                    Closing the preview window terminates the program.

AUTHOR:         Benjamin Whitsett
MODIFIED:       Dec. 19, 2024
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image, ImageOps
import os
import math

POPUP_NAME = 'Image Preview'

# custom pause that doesn't move the window to the front (https://stackoverflow.com/a/45734500)
def customPltPause(interval):
    backend = plt.rcParams['backend']
    if backend in mpl.rcsetup.interactive_bk:
        figManager = mpl._pylab_helpers.Gcf.get_active()
        if figManager is not None:
            canvas = figManager.canvas
            if canvas.figure.stale:
                canvas.draw()
            canvas.start_event_loop(interval)
            return

# expects `preview` dir to exist in the source directory,
#  returns None if not (or no valid images)
def getImage():
    try:
        x = os.listdir('preview') # exception if DNE
    except FileNotFoundError:
        return None
    if not x:
        return None
    
    path = os.path.join('preview', x[0])
    # verify copying is complete
    try:
        Image.open(path).verify()
    except Exception:
        return None
    
    # open and manage size of image
    img = Image.open(path)
    imgTransp = ImageOps.exif_transpose(img)
    img.close()
    k = 2**round(math.ceil(math.log2(imgTransp.width * imgTransp.height / 500000)/2))
    k = max(1, k)
    imgTransp = imgTransp.resize((imgTransp.width//k, imgTransp.height//k))
    os.remove(path)
    return imgTransp


def waitAndUpdate():
    while (img := getImage()) is None:
        customPltPause(0.1)
        if not plt.fignum_exists(POPUP_NAME):
            return False
    
    ax.clear()
    ax.imshow(img, extent=(0,img.width,0,img.height))
    ax.set_xlim(0, img.width)
    ax.set_ylim(0, img.height)
    ax.set_axis_off()
    fig.tight_layout()
    
    customPltPause(0.01)
    return plt.fignum_exists(POPUP_NAME)

if __name__ == '__main__':
    
    os.chdir(os.path.split(__file__)[0])
    mpl.rcParams['toolbar'] = 'None'
    fig, ax = plt.subplots(facecolor='#000', num=POPUP_NAME)
    plt.ion()
    plt.show()
    
    while waitAndUpdate():
        pass