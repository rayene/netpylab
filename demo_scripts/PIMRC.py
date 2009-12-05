import os
from scapy.layers import inet
from netpylab import World
from places import *
from paths import *
from nodes import *
from interfaces import *
from applications import *
from channels import *

world = World()

scenario = 4

if scenario == 1:   speed = 2
elif scenario == 2: speed = 2
else:               speed = 7

w.scenario = scenario

t = GpxPath('../gpx/rennes1.gpx', 'Rennes1')
c = Car(world, t, label='c')
a1 = Anchor(world, 48.119205, -1.650238, label='a1')
a2 = Anchor(world, 48.119205, -1.640238, label='a2')
a3 = Anchor(world, 48.124423,-1.627218, label='a3')
b1 = Building(world, 48.108205, -1.640238, label='b1')
b2 = Building(world, 48.102205, -1.625238, label='b2')
b3 = Building(world, 48.120103,-1.627092, label='b3')

c.start()

cable1 = EthernetCable(world)
if scenario <> 3:
    cable2 = EthernetCable(world)
cable3 = EthernetCable(world)

cable4 = EthernetCable(world)
cable5 = EthernetCable(world)


mn = MobileNodeMCoA(c, '2009::1', '2009::100', 'mn')
ap1 = WiFiAccessPoint(a1, 'ap1', channel = cable1)
if scenario <> 3: 
    ap2 = WiFiAccessPoint(a2, 'ap2', channel = cable2)
ap3 = WiMaxAccessPoint(a3, 'ap3', channel = cable3)
ar = IPRouter(b1, 'ar')
ha = HomeAgentMCoA(b2, '2009::100', '2009::', 64, 'ha')
cn = IPNode(b3, 'cn')


mn_i1 = WiFiInterface(mn, 'mn_i1')
mn_i2 = WiMaxInterface(mn, 'mn_i2')

ar_i1 = EthernetInterface(ar, 'ar_i1', channel = cable1)
if scenario <>3:
    ar_i2 = EthernetInterface(ar, 'ar_i2', channel = cable2)
ar_i3 = EthernetInterface(ar, 'ar_i3', channel = cable3)
ar_i4 = EthernetInterface(ar, 'ar_i4', channel = cable4)

ha_i1 = EthernetInterface(ha, 'ha_i1', channel = cable4)
ha_i2 = EthernetInterface(ha, 'ha_i2', channel = cable5)

cn_i1 = EthernetInterface(cn, 'cn_i1', channel = cable5)

ar_i1.ipv6.icmpv6.set_prefix_list([('2000:1::',64)])
if scenario <>3:
    ar_i2.ipv6.icmpv6.set_prefix_list([('2000:2::',64)])
ar_i3.ipv6.icmpv6.set_prefix_list([('2000:3::',64)])
ar_i4.ipv6.icmpv6.set_prefix_list([('2001::',64)])

ha_i1.ipv6.manual_addresses=['2001::100']
ha_i1.ipv6.icmpv6.set_prefix_list([('2001::',64)])
ha_i2.ipv6.manual_addresses=['2002::100']
ha_i2.ipv6.icmpv6.set_prefix_list([('2002::',64)])

cn_i1.ipv6.manual_addresses=['2002::1']

if scenario <>3:
    ar.rt6.manual_route_add('::', ar_i4, 0, next_hop = 'fe80::200:ff:fe00:d')
    ha.rt6.manual_route_add('::', ha_i1, 0, next_hop = 'fe80::200:ff:fe00:c')
else:
    ar.rt6.manual_route_add('::', ar_i4, 0, next_hop = 'fe80::200:ff:fe00:a')
    ha.rt6.manual_route_add('::', ha_i1, 0, next_hop = 'fe80::200:ff:fe00:9')    

alpha = 1280
beta = 2800
alpha = 12
beta = 28
wf1 = FTPClient(cn, '2009::1', None, 'wf1', interval = 0.08, dst_port=41, data_size = alpha)
wf2 = FTPClient(cn, '2009::1', None, 'wf2', interval = 0.08, dst_port=42, data_size = beta)

am1 = FTPServer(mn, 'am1', port=41)
am2 = FTPServer(mn, 'am2', port=42)

w.wf1 =wf1
w.wf2 =wf2


mn.start()
ap1.start()
if scenario <> 3:
    ap2.start()
    
ap3.start()
ar.start()
ha.start()
cn.start()


if world.gui:
    world.gui.target_obj = c
    world.gui.add_label(wf1.info)
    world.gui.add_label(am1.info)
    world.gui.map.zoom = 15
########################
# world.start(until=(1200+100)/speed)
world.start()
########################

f = open('/tmp/packets.txt', 'w')
f.write(w.packets.text())
f.close()
world.sequence_diagram([
                    (am1, am2, mn, mn_i1, mn_i2), 
                    (ap1.wireless_iface, ap1, ap1.ethernet_iface), 
                    (ap2.wireless_iface, ap2, ap2.ethernet_iface), 
                    (ap3.wireless_iface, ap3, ap3.ethernet_iface), 
                    (ar_i1, ar_i2, ar_i3, ar, ar_i4), 
                    (ha_i1, ha, ha_i2),
                    (cn_i1, cn, wf1, wf2)])

l1 = []
l2 = []
l3 = []
l4 = []
last1 = last2 = last3 = last4 = None
for p in world.packets:
    for trip_stop in p.trip:
        if trip_stop.action == 'retired' and trip_stop.actor == am1:
            lon = len(p[inet.UDP].payload)
            if last1:
                l1.append((trip_stop.time, trip_stop.time - last1, lon))
            last1 = trip_stop.time
        if trip_stop.action == 'retired' and trip_stop.actor == am2:
            lon = len(p[inet.UDP].payload)
            if last2:
                l2.append((trip_stop.time, trip_stop.time - last2, lon))
            last2 = trip_stop.time

        if trip_stop.action == 'sent' and trip_stop.actor == mn_i1:
            lon = len(p.data)
            if last3:
                l3.append((trip_stop.time, trip_stop.time - last3, lon))
            last3 = trip_stop.time     
        if trip_stop.action == 'sent' and trip_stop.actor == mn_i2:
            lon = len(p.data)
            if last4:
                l4.append((trip_stop.time, trip_stop.time - last4, lon))
            last4 = trip_stop.time


m1 = sum(a[1] for a in l1[4:])/len(l1)
m2 = sum(a[1] for a in l2[4:])/len(l2)
print 'MEAN1 = ', m1
print 'MEAN1 = ', m2

DATAFILE='data%i.txt' % scenario
f = open(DATAFILE, 'w')

# for t in l2[14:]:
#         f.write('%f %f %f %f\n' % (t[0], t[1], 1.280*8/t[1], 1.280*8/m2))




for i in range(max(int(l2[-1][0]), int(l1[-1][0]))):
    l_time = [(x[0], x[2]) for x in l1]
    a = 0
    for lt, ls in l_time:
        if lt >= i and lt < i+1:
            a+=ls
    l_time = [(x[0], x[2]) for x in l2]
    b = 0
    for lt, ls in l_time:
        if lt >= i and lt < i+1:
            b+=ls
    l_time = [(x[0], x[2]) for x in l3]
    c = 0
    for lt, ls in l_time:
        if lt >= i and lt < i+1:
            c+=ls
    l_time = [(x[0], x[2]) for x in l4]
    d = 0
    for lt, ls in l_time:
        if lt >= i and lt < i+1:
            d+=ls            
    f.write('%i %f %f %f %f\n' % (i, a*8.0/1000, b*8.0/1000, c*8.0/1000, d*8.0/1000))

f.close()

PLOTFILE1='troughput.png' 
f=os.popen('gnuplot' ,'w')
print >>f,  'set pointsize 1'
print >>f, "set xlabel 'time'; set ylabel 'Troughput'"
print >>f, "set terminal png large transparent size 800,600; set out '%s'" % PLOTFILE1
command = "plot '%s' u 1:2 w lines, '%s' u 1:3 w lines, '%s' u 1:4 w lines, '%s' u 1:5 w lines " % (DATAFILE, DATAFILE, DATAFILE, DATAFILE)
print >>f, command
f.flush()
time.sleep(1)
try:
    os.system('open '+ PLOTFILE1)
except:
    pass

#print mn_i1.info()
# print ar_i1.info()

