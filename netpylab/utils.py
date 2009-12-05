import os
import sys
import subprocess
import webbrowser

import config

def startfile(filepath):
    if sys.platform[:3] == 'win':
        os.startfile(filepath)
        return True
    elif sys.platform == 'darwin':
        subprocess.call('open', filepath)
        return True
    elif sys.platform.startswith('linux'):
        for command in ('gnome-open', 'kde-open', 'exo-open', 'xdg-open'):
            if webbrowser._iscommand(command):
                subprocess.call(command, filepath)
                return True
    return False
    

def default_class_img(a_class):
    for cls in a_class.__mro__:
        imgfile = os.path.join(config.SPRITES_FOLDER, cls.__name__ + '.png')
        if os.path.exists(imgfile):
            return imgfile

def wireshark(filepath):
    if webbrowser._iscommand('wireshark'):
        subprocess.call('wireshark', filepath)
        return True
    return False