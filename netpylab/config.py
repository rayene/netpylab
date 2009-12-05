import os

##################### Files & Folders #####################
IMG_FOLDER = 'img'
SPRITES_FOLDER = os.path.join(IMG_FOLDER, 'sprites')
BUTTONS_FOLDER = os.path.join(IMG_FOLDER, 'buttons')
LOGO = os.path.join(IMG_FOLDER, 'netpylab.png')
GPX_FOLDER = 'gpx'

MAP_CACHE_FOLDER = 'cache'
try:
    #try to put cache images in $HOME/cache
    MAP_CACHE_FOLDER = os.path.join(os.environ['HOME'], 'cache')
except:
    pass
##################### Files & Folders #####################