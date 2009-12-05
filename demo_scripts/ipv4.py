from netpylab import World
from places import *
from paths import *
from nodes import *
from interfaces import *
from applications import *
from channels import *

b5 = Building(world, 48.120205, -1.639238, label='b5')
t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
c1 = Car(world, t, label='c1')
n1 = HomeAgent(c1)
n2 = HomeAgent(b5)
i1 = WirelessInterface(n1)
i2 = WirelessInterface(n2)
i1.ip('10.0.0.1')
i2.ip('10.0.0.2')
l = WirelessChannel(world)

i1.connect(l)
i2.connect(l)

a1 = WhiteFountain(n1, '10.0.0.2')
a2 = BlackHole(n2)
i1.connect(l)
i2.connect(l)
a1.start(at = 3)
a2.start()

########################
world.start()
########################

world.packets.text()

world.packets.pdf('/tmp/packets.svg', [i1, i2])
if hasattr(world, 'win'):
    world.win.target_obj = c1
