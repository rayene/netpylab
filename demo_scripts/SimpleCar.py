import os
from netpylab import World
from places import *
from paths import *
from nodes import *
from interfaces import *
from applications import *
from channels import *

world = World()


t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
c = Car(world, t, label='c')
c.start(at=0)

# world.monitor.watch(lambda: c.speed, "Speed")

if world.gui:
    world.gui.target_obj = c
    world.gui.map.zoom = 15

world.start()
