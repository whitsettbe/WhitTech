"""
TITLE:          EXIF Image Labeler

DESCRIPTION:    Provides a user interface for managing and searching titles and
                    tags of EXIF-compatible images. Incompatible image types
                    are met with an offer to convert to a high-quality JPEG.
                    Autocompletes for tag entries are stored in the installation
                    directory at TagSuggestions.txt. More details are available
                    in the README. Written for Windows 11.

AUTHOR:         Benjamin Whitsett
MODIFIED:       Mar. 18, 2025
"""

import os
import inquirer # [sigh] documentation isn't great
import fileHandler
import subprocess
import time
from PIL import Image
from tqdm import tqdm
import winshell
import shutil

COMMENT_CHAR = '#'
DEFAULT_SUGGESTION_FILE = os.path.join(os.path.split(__file__)[0], 'TemplateSuggestions.txt')
SUGGESTION_FILE = os.path.join(os.path.split(__file__)[0], 'TagSuggestions.txt')

COMPATIBLE_IMAGE_TYPES = {'.jp2', '.j2k', '.jpf', '.jpm', '.jpg2', '.j2c', '.jpc', '.jpx', '.mj2',
                          '.jpg', '.jpeg', '.jpe', '.jif', '.jfif', '.jfi',
                          '.psd',
                          '.tiff', '.tif',
                          '.webp'}
CONVERSION_DEFAULT = '.jpeg'

"""
Utility functions
|
V
"""

# clear the windows terminal in which this is being run, and print the header
def clearTerminal():
    os.system('cls')
    print('---- Image Tag Editor ----')
    
    
# custom path cleanup
def cleanPath(path):
    return os.path.abspath(path.strip('"\''))

# custom directory validator
def customDirValidate(_, path):
    path = cleanPath(path)
    if not os.path.isdir(path):
        raise inquirer.errors.ValidationError('', reason=f'"{path}" is not a valid directory path.')
    return True

"""
Interface functions
|
V
"""
    
# try loading suggestions from the suggestion file, return whether we were successful
suggestions = []
def loadSuggestions():
    global suggestions
    if not os.path.exists(SUGGESTION_FILE):
        shutil.copyfile(DEFAULT_SUGGESTION_FILE, SUGGESTION_FILE)
    with open(SUGGESTION_FILE, 'r') as fin:
        lines = []
        for line in fin:
            line = line.strip()
            if not line or line[0] == COMMENT_CHAR:
                continue
            if fileHandler.TAG_DELIM_CHAR in line:
                return False
            lines.append(line)
            
    suggestions = lines
    return True
    
# open notepad to edit the suggestion file
def editSuggestionFile():
    clearTerminal()
    print('Edit Suggestions\n')
    print('The suggestion file will open in a new window.')
    print('Save and close the file once you are done editing it.')
    print(f'Note that any line which is blank or starts with "{COMMENT_CHAR}" will be ignored.')
    print(f'Make sure no subjectss contain the character "{fileHandler.TAG_DELIM_CHAR}".')
    
    proc = subprocess.Popen(['notepad', SUGGESTION_FILE], shell=True)# WINDOWS
    while proc.poll() is None:
        time.sleep(0.1)
    
    print()
    if loadSuggestions():
        print(f'{len(suggestions)} suggestions successfully loaded.')
    else:
        print('An error prevented the suggestions from loading.')
    input('\nPress Enter to return to the main menu.')
    return

# recursively get paths to all subfiles
runningSize = 0
def getSubimages(path, strict=False, resetCounter=True):
    global runningSize
    if resetCounter:
        runningSize = 0
    
    files = []
    folders = []
    try:
        for item in os.listdir(path):
            subpath = os.path.join(path, item)
            if os.path.isfile(subpath):
                
                # if not a compatible type, must do extra checks
                if not os.path.splitext(subpath)[1].lower() in COMPATIBLE_IMAGE_TYPES:
                    if strict:
                        continue
                    
                    # check if this file has already been converted
                    if os.path.isfile(os.path.splitext(subpath)[0] + CONVERSION_DEFAULT):
                        continue
                    
                    # check if this file is not an image
                    try:
                        with Image.open(subpath) as img:
                            img.verify()
                    except:
                        continue
                
                files.append(subpath)
                runningSize += os.path.getsize(subpath)
            else:
                folders.append(subpath)
    except PermissionError:
        pass
    
    files.sort(key = lambda x: x.lower())
    folders.sort(key = lambda x: x.lower())
    print('{:,} B'.format(runningSize), end='\r')
    for folder in folders:
        files += getSubimages(folder, strict, False)
    return files

# edit the titles and subjects on images in an indicated directory
def editTitlesAndTags():
    # get the source directory
    clearTerminal()
    print('Edit Titles And Subjects\n')
    path = cleanPath(inquirer.text('Directory containing images (may drag/drop)', validate=customDirValidate))
    
    # handle all files in the directory
    print('Enumerating...')
    filePaths = getSubimages(path)
    if not filePaths:
        input('\nNo images found. Press Enter for Main Menu.')
        return
    idx = 0
    lastChoice = None
    fh = None
    while True:
        idx = max(0, min(len(filePaths) - 1, idx))
        filePath = filePaths[idx]
        
        # offer to convert incompatible files (like PNG)
        ext = os.path.splitext(filePath)[1].lower()
        if ext not in COMPATIBLE_IMAGE_TYPES:
            # thanks to checks in getSubimages, we know this file was not yet converted and is definitely an image
            
            # print the file info
            clearTerminal()
            print('Edit Titles And Subjects\n')
            print(f'Directory: {os.path.split(filePath)[0]}')
            print(f'File name: {os.path.split(filePath)[1]}')
            print(f'{idx+1} / {len(filePaths)}')
            print()
            if fh is not None:
                fh.close()
                fh = None
            fileHandler.showFile(filePath)
            
            # present navigation menu
            choices = ['Next', 'Previous', 'Create EXIF-Compatible Version', 'Main Menu']
            try:
                selected = inquirer.list_input('Make a selection',
                            choices = choices, default = lastChoice, carousel=True)
            except KeyboardInterrupt:
                selected = choices[-1]
            lastChoice = selected
            
            if selected == choices[0]:
                idx += 1
            elif selected == choices[1]:
                idx -= 1
            elif selected == choices[2]: # convert to jpeg
                newFilePath = os.path.splitext(filePath)[0] + CONVERSION_DEFAULT
                try:
                    if os.path.exists(newFilePath): # this shouldn't ever be true
                        confirm = inquirer.confirm(f'This will overwrite the file {os.path.split(newFilePath)[1]} with data from {os.path.split(filePath)[1]}. Continue?', default=True)
                    else:
                        confirm = True
                except KeyboardInterrupt:
                    continue
                
                if confirm:
                    img = Image.open(filePath)
                    imgConv = img.convert('RGB')
                    img.close()
                    imgConv.save(newFilePath, quality=95)
                    filePaths[idx] = newFilePath
                
            elif selected == choices[3]:
                fileHandler.closePreview()
                raise KeyboardInterrupt()
        
        else: # edit title and subjects
            
            # check if this file is not an image
            try:
                with Image.open(filePath) as img:
                    img.verify()
            except:
                filePaths.pop(idx)
                continue
            
            # print the file info
            clearTerminal()
            print('Edit Titles And Subjects\n')
            print('(May be incompatible with Windows native tag editing)\n')
            print(f'Directory: {os.path.split(filePath)[0]}')
            print(f'File name: {os.path.split(filePath)[1]}')
            print(f'{idx+1} / {len(filePaths)}')
            print()
            if fh is None:
                fh = fileHandler.FileHandler(filePath)
            
            # print the title and subject info
            print(f'Title: {fh.getTitle()}')
            tagStr = ("\n"+" "*6).join(fh.getTags())
            print(f'Subjects: {tagStr}')
            print()
            choices = ['Next', 'Previous', 'Edit Title', 'Add Subject', 'Remove Subject', 'Main Menu']
            try:
                selected = inquirer.list_input('Make a selection',
                            choices = choices, default = lastChoice, carousel=True)
            except KeyboardInterrupt:
                selected = choices[-1]
            lastChoice = selected
            
            if selected == choices[0]: # Next image
                fh.close()
                fh = None
                idx += 1
                
            elif selected == choices[1]: # Previous image
                fh.close()
                fh = None
                idx -= 1
                
            elif selected == choices[2]: # Title editor
                try:
                    fh.setTitle(inquirer.text('New title', default=fh.getTitle()))
                except KeyboardInterrupt:
                    continue
                
            elif selected == choices[3]: # Tag/subject adder
                
                def validate(answers, current):
                    current = current.strip()
                    message = fileHandler.isInvalidTag(current)
                    if message:
                        raise inquirer.errors.ValidationError("", reason=message)
                    if current in fh.getTags():
                        raise inquirer.errors.ValidationError("", reason=f'Subject "{current}" already exists in this file.')
                    return True
                
                lastAutoPre = ''
                def autocomplete(text, state):
                    nonlocal lastAutoPre # bind to nearest external
                    if state == 0:
                        lastAutoPre = text
                    guesses = [s for s in suggestions if s.lower().startswith(lastAutoPre.lower())]
                    guesses.sort(key = lambda x: x.lower())
                    return guesses[state%len(guesses)] if guesses else text
                
                try:
                    fh.addTag(inquirer.text('Subject to add (use Tab to cycle suggestions)', validate=validate, autocomplete=autocomplete).strip())
                except KeyboardInterrupt:
                    continue
                
            elif selected == choices[4]: # Subject remover
                
                def validate(answers, current):
                    if not current:
                        return True
                    if current not in fh.getTags():
                        raise inquirer.errors.ValidationError("", reason=f'Subject "{current}" does not exist in this file.')
                    return True
                
                lastAutoPre = ''
                def autocomplete(text, state):
                    nonlocal lastAutoPre # bind to nearest external
                    if state == 0:
                        lastAutoPre = text
                    guesses = [s for s in fh.getTags() if s.lower().startswith(lastAutoPre.lower())]
                    guesses.sort(key = lambda x: x.lower())
                    return guesses[state%len(guesses)] if guesses else text
                
                try:
                    fh.removeTag(inquirer.text('Subject to remove (use Tab to cycle suggestions)', validate=validate, autocomplete=autocomplete))
                except KeyboardInterrupt:
                    continue
            
            else: # Return to main menu
                fh.close()
                fh = None
                fileHandler.closePreview()
                raise KeyboardInterrupt()
            
# search for keywords in the titles and subjects of images in the indicated directory
def searchTitlesAndTags():
    # get the source directory
    clearTerminal()
    print('Search Titles And Subjects\n')
    path = cleanPath(inquirer.text('Directory to search (may drag/drop)', validate=customDirValidate))
    
    # get the keywords
    keywords = []
    lastChoice = None
    while True:
        clearTerminal()
        print('Search Titles And Subjects\n')
        print('Keywords:', ('\n' + ' '*10).join(keywords))
        print()
        choices = ['Add Keyword', 'Remove Keyword', 'Search', 'Main Menu']
        
        def validate(answers, current):
            if current == choices[2] and not keywords:
                raise inquirer.errors.ValidationError("", reason=f'You must provide at least one keyword.')
            return True
        
        selected = inquirer.list_input('Make a selection',
                    choices = choices, default = lastChoice, validate=validate, carousel=True)
        lastChoice = selected
        
        if selected == choices[0]: # add keyword
            
            def validate(answers, current):
                current = current.strip()
                if current in keywords:
                    raise inquirer.errors.ValidationError("", reason=f'Keyword "{current}" was already listed.')
                return True
            
            lastAutoPre = ''
            def autocomplete(text, state):
                nonlocal lastAutoPre # bind to nearest external
                if state == 0:
                    lastAutoPre = text
                guesses = [s for s in suggestions if s.lower().startswith(lastAutoPre.lower())]
                guesses.sort(key = lambda x: x.lower())
                return guesses[state%len(guesses)] if guesses else text
            
            toAdd = inquirer.text('Keyword to add (use Tab to cycle suggestions)', validate=validate, autocomplete=autocomplete).strip()
            if toAdd:
                keywords.append(toAdd)
                
        elif selected == choices[1]: # remove keyword
            
            def validate(answers, current):
                current = current.strip()
                if not current:
                    return True
                if current not in keywords:
                    raise inquirer.errors.ValidationError("", reason=f'Keyword "{current}" was not listed.')
                return True
            
            lastAutoPre = ''
            def autocomplete(text, state):
                nonlocal lastAutoPre # bind to nearest external
                if state == 0:
                    lastAutoPre = text
                guesses = [s for s in keywords if s.lower().startswith(lastAutoPre.lower())]
                guesses.sort(key = lambda x: x.lower())
                return guesses[state%len(guesses)] if guesses else text
            
            toRemove = inquirer.text('Keyword to remove (use Tab to cycle suggestions)', validate=validate, autocomplete=autocomplete).strip()
            if toRemove:
                keywords.remove(toRemove)
                
        elif selected == choices[2]: # search
            break
            
        elif selected == choices[3]: # main menu
            raise KeyboardInterrupt()
        
    # start the search
    clearTerminal()
    print('Search Titles And Subjects\n')
    print('Enumerating...')
    filePaths = getSubimages(path, strict=True)
    filePaths = [f for f in filePaths if os.path.splitext(f)[1].lower() in COMPATIBLE_IMAGE_TYPES]
    print('\nSearching...')
    keepers = []
    totSize = 0
    aliases = []
    aliasSet = set()
    for f in tqdm(filePaths):
        if all([fileHandler.checkForKeyword(f, k) for k in keywords]):
            keepers.append(f)
            totSize += os.path.getsize(f)
            
            # generate a unique alias for the file
            alias = lambda s: os.path.splitext(os.path.split(f)[1])[0] + s + os.path.splitext(f)[1]
            suffix = ''
            while alias(suffix) in aliasSet:
                if suffix:
                    suffix = '_' + str(1+int(suffix[1:]))
                else:
                    suffix = '_2'
            aliases.append(alias(suffix))
            aliasSet.add(aliases[-1])
            
    # report results to user
    clearTerminal()
    print('Search Titles and Subjects\n')
    print(f'{len(keepers)} files found.\n')
    def validate(answers, current):
        customDirValidate(answers, current) # ensure existent dir
        current = cleanPath(current)
        if os.listdir(current): # ensure empty
            raise inquirer.errors.ValidationError('', reason=f'Directory "{current}" must be empty.')
        return True
    targDir = cleanPath(inquirer.text('Empty folder where results should be placed (may drag/drop)', validate=validate))
    print()
    
    # choose result mode
    choices = [f'Shortcuts (<{round(3*len(keepers)/1024., 3)} MB, more cumbersome to access)', f'Copies ({round(totSize/2**20., 3)} MB, easier to access)']
    selected = inquirer.list_input('Choose output mode',
                choices = choices, default = choices[0], carousel=True)
    
    # make shortcuts or copies
    if selected == choices[0]: # shortcuts
        for source, alias in tqdm(list(zip(keepers, aliases))):
            shortcut = winshell.shortcut(os.path.join(targDir, alias + '.lnk'))
            shortcut.path = source
            shortcut.description = alias
            shortcut.write()
    
    else: # copies
        for source, alias in tqdm(list(zip(keepers, aliases))):
            shutil.copyfile(source, os.path.join(targDir, alias))
            
    os.startfile(targDir)
    input('\nResults loaded!\nPress Enter to return to the main menu.')
    return

# call git to update the software
def update():
    clearTerminal()
    print('Updating...')
    os.system('git pull')
    print('\nUpdate complete!\n\nPlease restart the program now.')
    while True:
        try:
            input()
        except KeyboardInterrupt:
            pass
    
    
if __name__ == '__main__':

    loadSuggestions()
    lastChoice = None
    while True:
        try:
            clearTerminal()
            
            print('Main Menu (use Ctrl+C to return here, Ctrl+Shift+C to copy)')
            print()
            
            choices = [f'View/Edit Suggestions ({len(suggestions)} currently loaded)', 'Edit Titles And Subjects', 'Search Titles And Subjects', 'Update', 'Exit']
            if lastChoice is None:
                lastChoice = choices[-1]
            selected = inquirer.list_input('Make a selection with the arrow keys and press Enter',
                        choices = choices, default = lastChoice, carousel=True)
            lastChoice = selected
            
            if selected == choices[0]:
                editSuggestionFile()
            elif selected == choices[1]:
                editTitlesAndTags()
            elif selected == choices[2]:
                searchTitlesAndTags()
            elif selected == choices[3]:
                update()
            else:
                break
            
        except KeyboardInterrupt:
            pass
