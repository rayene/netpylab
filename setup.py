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
    name='netpylab',
    version='0.7',
    description='The python networking laboratory',
    author='Rayene Ben Rayana',
    author_email='rayene.benrayana@gmail.com',
    url = 'http://github.com/rayene/netpylab',
    packages=['netpylab'],
    app=APP,
    data_files=DATA_FILES,
    options=OPTIONS,
    setup_requires=REQUIRES,
    long_description = """  """,
    classifiers=[
          "Topic :: Internet",
          "Topic :: Education",
          "Topic :: Scientific/Engineering",
          "Topic :: Communications",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          'Environment :: Console',
          "Programming Language :: Python",
          "Development Status :: 2 - Pre-Alpha",
          "Intended Audience :: Developers",
          "Intended Audience :: Education",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "Intended Audience :: Telecommunications Industry",
          "Natural Language :: English",
          "Operating System :: OS Independent"],
    keywords='network simulation emulation',
    license='GPL',
    # install_requires=[
                    # 'scapy', 
                    # 'wxPython',
                    # ]
                    )
    

    
      