import os
from netpylab import World, DeltaMonitor
from places import *
from paths import *
from nodes import IPNode, IPRouter
from interfaces import *
from applications import *
from channels import *

world = World()

b1 = Building(world, 48.120205, -1.639238, label='b1')
b2 = Building(world, 48.130205, -1.639238, label='b2')

n1 = IPNode(b1, 'n1')
n2 = IPNode(b2, 'n2')

i1 = EthernetInterface(n1, 'i1')
i2 = EthernetInterface(n2, 'i2')

l = EthernetCable(world)

i1.connect(l)
i2.connect(l)

# wf = WhiteFountain(n1, 'fe80::200:ff:fe00:2', i1, 'wf1')
# bh = BlackHole(n2, 'bh1')

wf = Client(n1, '2001::200:ff:fe00:2', 'tcp', i1, 'wf1')
bh = Server(n2, 'bh1')

# DeltaMonitor(world, lambda: wf.i,label = "wf sent", color = 'red')
# world.monitor.watch(lambda: wf.i, "wf sent", 'red')
# world.monitor.watch(lambda: bh.received, "bh received", 'blue')

n1.start()
n2.start()


if world.gui:
    world.gui.target_obj = b1
    world.gui.map.zoom = 15
    # world.gui.add_label(wf.info)
    # world.gui.add_label(bh.info)

########################
world.start()
########################

# world.sequence_diagram([(wf, n1, i1), (i2, n2, bh)])

# f = open('/tmp/packets.txt', 'w')
# f.write(w.packets.text())
# f.close()
# 
# world.packets.svg('/tmp/packets.svg', [(wf, n1, i1), (i2, n2, bh)])
# print i1.info()
# print i2.info()
