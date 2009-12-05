from netpylab import World
from places import *
from paths import *
from nodes import *
from interfaces import *
from applications import *
from channels import *

print world
b0 = Building(world, 0.0, 0.0, label='b0')
b1 = Building(world, 84.0, -180.0, label='b1')
b2 = Building(world, 84.0, 180.0, label='b2')
b3 = Building(world, -84.0, -180.0, label='b3')
# 
b4 = Building(world, -84.0, 180.0, label='b4')

b5 = Building(world, 48.120205, -1.639238, label='b5')
# b5 = Building(world, -84.0, -170.0, label='b5')


#t = GpxPath('../gpx/nztrip-tracks.gpx', '08-JAN-06 02', 10)
t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
#t = GpxPath('../gpx/periph_rennes.gpx')
#t = GpxPath('../gpx/rennes_geant.gpx')
#t = GpxPath('../gpx/250128.gpx', 0, 3)
c1 = Car(world, t, label='c1')
# 
n1 = HomeAgent(c1)
n2 = HomeAgent(b5)
<<<<<<< .mine
#i1 = WirelessInterface(n1)
#i2 = WirelessInterface(n2)
#i1.ip('10.0.0.1')
=======
i1 = WirelessInterface(n1)
i2 = WirelessInterface(n2)
i1.ip('10.0.0.1')
>>>>>>> .r87
# l1 = Loopback(n1)
# 
# n2 = IPNode(b1)
#i2 = RealInterface(n2, 'en1')
#i2.start(at = 3, lifetime = 18)
#i2.ip('10.0.0.2')
# l2 = Loopback(n2)
# 
#l = WirelessLink(world)
#i1.channel = l
#i2.channel = l
#l.interfaces = [i1, i2]
# 
#a1 = WhiteFountain(n1, '10.0.0.2')
#a2 = BlackHole(n2)
#a2 = WhiteFountain(n2, '100::1')
# i1.ip('100::2', family='inet6')
# i2.ip('100::2', family='inet6')
# 
#i1.connect(l)
#i2.connect(l)
#a1.start()
#a2.start()
# 
# #    print n1.rt4
# #    print n2.rt4
world.start()
# 
# 
if hasattr(world, 'win'):
    world.win.target_obj = c1
