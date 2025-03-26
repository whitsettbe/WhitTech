import importlib
import sys
import os

DEPEND = [
        'inquirer',     # 3.4.0
        'pillow',       # 9.5.0
        'tqdm',         # 4.65.0
        'winshell',     # 0.6
        'matplotlib',   # 3.10.1
        'pyexiv2',      # 2.15.3
        'pywin32',      # 308
        ]

# install python dependencies
for dep in DEPEND:
    if importlib.util.find_spec(dep) == None:
        os.system('"' + sys.executable + '" -m pip install '+dep)