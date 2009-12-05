"""
py2app/py2exe build script for NetPyLab.
Usage (Mac OS X):
    python setup.py py2app
Usage (Windows):
    python setup.py py2exe
"""

import os, sys
from setuptools import setup

APP = [os.path.join('netpylab','netpylab.py')]
DATA_FILES = [os.path.join('netpylab','img'), 'scripts', 'gpx']

if sys.platform == 'darwin':
    OPTIONS = {'py2app' : 
        {'argv_emulation': True, 
        'iconfile': 'netpylab.icns',
        'plist'   : 'Info.plist'}}
    REQUIRES = ['py2app']
elif sys.platform[:3] == 'win':
    OPTIONS = {'py2exe' : {}}
    REQUIRES = ['py2exe']
else:
    OPTIONS = {}
    REQUIRES = []

setup(
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=REQUIRES,
)
