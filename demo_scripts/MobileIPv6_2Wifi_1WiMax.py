import os
from netpylab import World
from places import *
from paths import *
from nodes import *
from interfaces import *
from applications import *
from channels import *
# from report import Report
from layers.ipv6 import mac2linklocal

world = World()

t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
c = Car(world, t, label='c')
a1 = Anchor(world, 48.113205, -1.649238, label='a1')
a2 = Anchor(world, 48.120205, -1.636238, label='a2')
a3 = Anchor(world, 48.124423,-1.627218, label='a3')
b1 = Building(world, 48.108205, -1.640238, label='b1')
b2 = Building(world, 48.102205, -1.625238, label='b2')
b3 = Building(world, 48.120103,-1.627092, label='b3')

c.start(at=0)

cable1 = EthernetCable(world)
cable2 = EthernetCable(world)
cable3 = EthernetCable(world)
cable4 = EthernetCable(world)
cable5 = EthernetCable(world)

mn = MobileNode(c, '2009::1', '2009::100', 'mn')
ap1 = WiFiAccessPoint(a1, 'ap1', channel = cable1)
ap2 = WiFiAccessPoint(a2, 'ap2', channel = cable2)
ap3 = WiMaxAccessPoint(a3, 'ap3', channel = cable3)
ar = IPRouter(b1, 'ar')
ha = HomeAgent(b2, '2009::100', '2009::', 64, 'ha')
cn = IPNode(b3, 'cn')


mn_i1 = WiFiInterface(mn, 'mn_i1')
mn_i2 = WiMaxInterface(mn, 'mn_i2')

ar_i1 = EthernetInterface(ar, 'ar_i1', channel = cable1)
ar_i2 = EthernetInterface(ar, 'ar_i2', channel = cable2)
ar_i3 = EthernetInterface(ar, 'ar_i3', channel = cable3)
ar_i4 = EthernetInterface(ar, 'ar_i4', channel = cable4)

ha_i1 = EthernetInterface(ha, 'ha_i1', channel = cable4)
ha_i2 = EthernetInterface(ha, 'ha_i2', channel = cable5)

cn_i1 = EthernetInterface(cn, 'cn_i1', channel = cable5)

ar_i1.ipv6.icmpv6.set_prefix_list([('2000:1::',64)])
ar_i2.ipv6.icmpv6.set_prefix_list([('2000:2::',64)])
ar_i3.ipv6.icmpv6.set_prefix_list([('2000:3::',64)])
ar_i4.ipv6.icmpv6.set_prefix_list([('2001::',64)])

ha_i1.ipv6.manual_addresses=['2001::100']
ha_i1.ipv6.icmpv6.set_prefix_list([('2001::',64)])
ha_i2.ipv6.manual_addresses=['2002::100']
ha_i2.ipv6.icmpv6.set_prefix_list([('2002::',64)])

cn_i1.ipv6.manual_addresses=['2002::1']

ha_i1_addr = mac2linklocal(ha_i1.mac)
ar_i4.ipv6.manual_route_add('::', ar_i4, 0, next_hop = ha_i1_addr)
ar_i4_addr = mac2linklocal(ar_i4.mac)
ha_i1.ipv6.manual_route_add('::', ha_i1, 0, next_hop = ar_i4_addr)

# ar.rt6.manual_route_add('::', ar_i4, 0, next_hop = 'fe80::200:ff:fe00:d')
# ha.rt6.manual_route_add('::', ha_i1, 0, next_hop = 'fe80::200:ff:fe00:c')

mn.start(at = 1)
ap1.start(at = 1)
ap2.start(at = 1)
ap3.start(at = 1)
ar.start(at = 1)
ha.start(at = 1)
cn.start(at = 1)


wf = WhiteFountain(mn, '2002::1', None, 'wf')
am = AnsweringMachine(cn, 'am')
wf.start(0)
am.start(0)

DeltaMonitor(world, lambda: wf.i,label = "wf sent", color = 'red')


if world.gui:
    world.gui.target_obj = c
    world.gui.add_label(wf.info)
    world.gui.add_label(am.info)
    world.gui.map.zoom = 15


world.start()


world.sequence_diagram([
            (mn, mn_i1, mn_i2), 
            (ap1.wireless_iface, ap1, ap1.ethernet_iface), 
            (ap2.wireless_iface, ap2, ap2.ethernet_iface), 
            (ap3.wireless_iface, ap3, ap3.ethernet_iface), 
            (ar_i1, ar_i2, ar_i3, ar, ar_i4), 
            (ha_i1, ha, ha_i2),
            (cn_i1, cn)
            ])


