import os
from netpylab import World
from places import *
from paths import *
from nodes import IPNode, IPRouter, AccessPoint
from interfaces import *
from applications import *
from channels import *

world = World()

t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
c = Car(world, t, label='c')
a = Anchor(world, 48.113205, -1.649238, label='a')
b = Building(world, 48.120205, -1.639238, label='b')

c.start(at=0)

n1 = IPNode(c, 'n1')
n2 = IPNode(b, 'n2')
i1 = WiFiInterface(n1, 'i1')

cable = EthernetCable(world)
i2 = EthernetInterface(n2, 'i2', channel = cable)
ap1 = AccessPoint(a, 'ap1', channel = cable)

wf = WhiteFountain(n1, 'fe80::200:ff:fe00:2', i1, 'wf1')
bh = BlackHole(n2, 'bh1')

n1.start()
n2.start()
ap1.start()


if world.gui:
    world.gui.map.zoom = 15
    world.gui.target_obj = c
    world.gui.add_label(wf.info)
    world.gui.add_label(bh.info)

########################
world.start()
########################

i1.info()
i2.info()

