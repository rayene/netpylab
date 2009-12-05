import os
from netpylab import World
from places import *
from paths import *
from nodes import *

t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
c = Car(world, t, label='c')
c.start(at=0)
a1 = Anchor(world, 48.116205, -1.647238, label='a1')
a2 = Anchor(world, 48.119205, -1.640238, label='a2')
a3 = Anchor(world, 48.124423,-1.627218, label='a3')

ap1 = WiFiAccessPoint(a1, 'ap1')
ap2 = WiFiAccessPoint(a2, 'ap2')

if hasattr(world, 'win'):
    world.win.target_obj = c
    world.win.zoom = 15
########################
world.start()
########################
