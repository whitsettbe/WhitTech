PROJECT TITLE:      WhitTech Photo Tagger

WARNING:            Not yet portable, not yet cross-platform

DEPENDENCIES:       This program requires a Python3 instance with several
                        non-default libraries installed. They can be added
                        with the command:
                            python -m pip install inquirer matplotlib pillow \
                                    tqdm pywin32 winshell pyexiv2

STARTUP:            To run the program, execute the following command:
                            python main.py
                    where `python` refers to an installed copy of Python 3.
                    Prompts will then be given through the command line.

COMPATIBILITY:      This program was tested on Windows 11 with Python 3.11.4.

AUTHORS:            Benjamin Whitsett
                    whitsettbe@gmail.com

MODIFIED:           Mar. 25, 2025


PURPOSE:            This program allows for easy modification of title and
                    tag data in EXIF-compatible images, as well as searching
                    through said data. Titles are stored in XPTitle, and
                    tags are stored (semicolon (+space) as separator) in
                    XPSubject. Autocomplete tags are stored in the file
                    TagSuggestions.txt, which can be edited in a Notepad
                    window created by the program. Lines which are blank or
                    start with a # are ignored in the suggestions file,
                    and thus can be used for easy sectioning and labeling
                    of suggestions.

                    Note that in tag editing, a file which is not compatible
                    with EXIF (like PNG) will give the option of creating a
                    JPEG copy. However, any file which is not EXIF-compatible
                    will be ignored if there is another file with the same
                    name in the same folder with the extension '.jpeg'. This
                    effectively allows the pre-conversion file version to be
                    skipped under most circumstances, but may have unwanted
                    side-effects in certain file labeling systems.

                    Search results can generate either a folder of shortcuts
                    (very small, but hard to use) or a folder of actual
                    file copies.

ERRORS:             Should the program crash unexpectedly, contact the
                        developer with any questions.