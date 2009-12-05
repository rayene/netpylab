from netpylab import World
from places import *
from paths import *
from nodes import *
from interfaces import *
from applications import *
from channels import *
from report import Report
from ipv6 import mac2linklocal

world = World()

t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
c = Car(world, t, label='c')
a1 = Anchor(world, 48.113205, -1.649238, label='a1')
a2 = Anchor(world, 48.114447,-1.63994, label='a2')
b1 = Building(world, 48.120205, -1.644238, label='b1')
b2 = Building(world, 48.122205, -1.644238, label='b2')
b3 = Building(world, 48.122205, -1.636238, label='b3')

c.start(at=0)


cable1 = EthernetCable(world)
cable2 = EthernetCable(world)
cable3 = EthernetCable(world)
cable4 = EthernetCable(world)

mn = MobileNode(c, '2009::1', '2009::100', 'mn')
ap1 = AccessPoint(a1, 'ap1', channel = cable1)
ap2 = AccessPoint(a2, 'ap2', channel = cable2)
ar = IPRouter(b1, 'ar')
ha = HomeAgent(b2, '2009::100', '2009::', 64, 'ha')
cn = IPNode(b3, 'cn')



mn_i1 = WiFiInterface(mn, 'mn_i1')
ar_i1 = EthernetInterface(ar, 'ar_i1', channel = cable1)
ar_i2 = EthernetInterface(ar, 'ar_i2', channel = cable2)
ar_i3 = EthernetInterface(ar, 'ar_i3', channel = cable3)
ha_i1 = EthernetInterface(ha, 'ha_i1', channel = cable3)
ha_i2 = EthernetInterface(ha, 'ha_i2', channel = cable4)
cn_i1 = EthernetInterface(cn, 'cn_i1', channel = cable4)

ar_i1.ipv6.icmpv6.set_prefix_list([('2000:1::',64)])
ar_i2.ipv6.icmpv6.set_prefix_list([('2000:2::',64)])
ar_i3.ipv6.icmpv6.set_prefix_list([('2001::',64)])

ha_i1.ipv6.manual_addresses=['2001::100']
ha_i1.ipv6.icmpv6.set_prefix_list([('2001::',64)])
ha_i2.ipv6.manual_addresses=['2002::100']
ha_i2.ipv6.icmpv6.set_prefix_list([('2002::',64)])

cn_i1.ipv6.manual_addresses=['2002::1']

ha_i1_addr = mac2linklocal(ha_i1.mac)
ar_i3.ipv6.manual_route_add('::', ar_i3, 0, next_hop = ha_i1_addr)
ar_i3_addr = mac2linklocal(ar_i3.mac)
ha_i1.ipv6.manual_route_add('::', ha_i1, 0, next_hop = ar_i3_addr)

mn.start()
ap1.start()
ar.start()
ha.start()
cn.start()


wf = WhiteFountain(mn, '2002::1', None, 'wf')
am = AnsweringMachine(cn, 'am')

world.monitor.watch(lambda: wf.i, "wf sent", 'red')
world.monitor.watch(lambda: am.received, "am received", 'blue')

wf.start()
am.start()

if World.gui:
    world.gui.target_obj = c
    world.gui.add_label(wf.info)
    world.gui.add_label(am.info)
    world.gui.map.zoom = 15
    
########################
world.start()
########################
# print 'Producing Report ... '
world.sequence_diagram([(mn, mn_i1), (ap1.wireless_iface, ap1, ap1.ethernet_iface), (ap2.wireless_iface, ap2, ap2.ethernet_iface), (ar_i1, ar_i2, ar, ar_i3), (ha_i1, ha, ha_i2),(cn_i1, cn)])
# os.system("open /tmp/packets.pdf")

