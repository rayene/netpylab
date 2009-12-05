import os
from netpylab import World
from places import *
from paths import *
from nodes import IPNode, IPRouter
from interfaces import *
from applications import *
from channels import *

world = World()

b1 = Building(world, 48.120205, -1.639238, label='b1')
b2 = Building(world, 48.120205, -1.644238, label='b2')
b3 = Building(world, 48.120205, -1.649238, label='b3')

n1 = IPNode(b1, 'n1')
n2 = IPNode(b3, 'n2')
r = IPRouter(b2, 'Router')

i1 = EthernetInterface(n1, 'i1')
i1.manual_addresses=['2010::1', '2011::1']

ir1 = EthernetInterface(r, 'ir1')
ir1.ipv6.icmpv6.set_prefix_list([('2010::',64), ('2011::',64)])

ir2 = EthernetInterface(r, 'ir2')
ir2.ipv6.icmpv6.set_prefix_list([('2100::',64), ('2101::',64)])

i2 = EthernetInterface(n2, 'i2')
i2.ipv6.manual_addresses=['2100::1', '2101::1']


l1 = EthernetCable(world)
l2 = EthernetCable(world)

ir1.connect(l1)
ir2.connect(l2)

i1.connect(l1)
i2.connect(l2)

wf = WhiteFountain(n1, '2100::1', label='wf')
bh = BlackHole(n2, label=  'bh')

r.start()
n1.start()
n2.start()


if world.gui:
    world.gui.map.zoom = 15
    world.gui.target_obj = b1
    world.gui.add_label(wf.info, 560,38)
    world.gui.add_label(bh.info, 560,18)

########################
world.start()
########################


# f = open('/tmp/packets.txt', 'w')
# f.write(w.packets.text())
# f.close()
# 
# world.packets.svg('/tmp/packets.svg', 
#                         [
#                         (wf, n1, i1),
#                         (ir1, r, ir2),
#                         (i2, n2, bh)
#                          ])
# print i1.info()
# print i2.info()
# os.system("/Applications/Inkscape.app/Contents/Resources/bin/inkscape --without-gui --vacuum-defs --export-pdf=/tmp/packets.pdf /tmp/packets.svg &> /dev/null")
# os.system("open /tmp/packets.pdf")
