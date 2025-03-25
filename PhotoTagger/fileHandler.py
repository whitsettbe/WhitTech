"""
TITLE:          EXIF File Handler

DESCRIPTION:    Provides utility functions for interaction with image files'
                    EXIF data. Titles are stored under XPTitle and tags are
                    stored under XPSubject, and are separated by semicolons
                    (and, optionally, whitespace around the semicolons). Ties to
                    `viewer.py` are also provided for controlling a separate
                    preview process.

AUTHOR:         Benjamin Whitsett
MODIFIED:       Mar. 18, 2025
"""

import pyexiv2
import os
import sys
import shutil
import subprocess
import re

TITLE_LOC = 'Exif.Image.XPTitle'
TAG_LOC = 'Exif.Image.XPSubject'

TAG_DELIM_CHAR = ';'
TAG_DELIM_DEFAULT = '; '
TAG_DELIM_RE = r'\s*;\s*'

PREVIEW_DIR_LOC = os.path.join(os.path.split(__file__)[0], 'preview')
PREVIEW_CODE_LOC = os.path.join(os.path.split(__file__)[0], 'viewer.py')

# create the `preview` folder in the source dir, prompting the viewer (runs automatically)
previewProc = None
def initPreview():
    global previewProc
    try:
        os.mkdir(PREVIEW_DIR_LOC)
    except FileExistsError:
        pass
    previewProc = subprocess.Popen([sys.executable, PREVIEW_CODE_LOC], start_new_session=True)

# pass a file to the previewer (initPreview should be called first)
def showFile(path):
    if previewProc is None or previewProc.poll() is not None:
        initPreview()
    shutil.copyfile(path, os.path.join(PREVIEW_DIR_LOC, os.path.split(path)[1]))
    
    
# delete the `preview` folder, to cancel the viewer program (should be called manually)
def closePreview():
    global previewProc
    if previewProc is not None:
        previewProc.kill()
        previewProc = None
        
        
# is tag valid? (return message to use in exception)
def isInvalidTag(tag):
    return f'Character "{TAG_DELIM_CHAR}" is not allowed in tag "{tag}"' if TAG_DELIM_CHAR in tag else ''

# quietly check a file for a keyword in the title/tags
def checkForKeyword(path, keyword):
    im = pyexiv2.Image(path)
    exifData = im.read_exif()
    title = exifData.get(TITLE_LOC, '')
    tags = exifData.get(TAG_LOC, '')
    im.close()
    return keyword in title or keyword in tags

# clean a tag (removing null bytes)
def tagClean(s):
    return ''.join(filter(lambda c: ord(c) != 0, s))

# handle the title/tag editing and displaying of a file
class FileHandler:
    
    # read the image, initialize title/tags, and prompt the viewer
    def __init__(self, path):
        # read the image
        self.path = path
        self.image = pyexiv2.Image(path)
        
        # load tags and title
        exifData = self.image.read_exif()
        self.title = tagClean(exifData.get(TITLE_LOC, ''))
        self.tags = re.split(TAG_DELIM_RE, tagClean(exifData.get(TAG_LOC, '')))
        if '' in self.tags:
            self.tags.remove('')
        self.tags.sort()
        
        # display the file
        showFile(path)
    
    # title getter
    def getTitle(self):
        return self.title
    
    # title setter
    def setTitle(self, title):
        self.title = title
        
    # tag getter (copy of tag list)
    def getTags(self):
        return list(self.tags)
    
    # tag remover (no errors)
    def removeTag(self, tag):
        try:
            self.tags.remove(tag)
        except ValueError:
            pass
        
    # add a valid non-empty tag
    def addTag(self, tag):
        if not isInvalidTag(tag) and len(tag) > 0:
            self.tags.append(tag)
            self.tags.sort()
        
    # save the edited title/tags to the file
    def close(self):
        assert self.path is not None
        
        self.image.modify_exif({TITLE_LOC: self.title,
                                TAG_LOC: TAG_DELIM_DEFAULT.join(self.tags)})
        self.image.close()
        self.path = None
        
if __name__ == '__main__':
    fh = FileHandler('testPics\\dining.jpg')