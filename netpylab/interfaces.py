#!/usr/bin/env python
# -*- coding: utf-8 -*-

import netpylab

import channels
from scapy.layers import l2, dot11, inet6
#from scapy.data import ETHER_BROADCAST
from scapy.sendrecv import sniff, send

# import scapy.config
from packets import Packet


class Interface(netpylab.NetpylabObject):
    """A network card, network adapter or NIC (network interface card) is a
    piece of computer hardware designed to allow computers to communicate over
    a computer network. It provides physical access to a networking medium
    and often provides a low-level addressing system through the use of MAC
    addresses. It allows users to connect to each other either by using
    cables or wirelessly.The NIC provides the transfer of data in megabytes.
    """

    mac_pool=0
    def new_mac(self):
        Interface.mac_pool += 1
        return '00:00:00:00:%02x:%02x' % (self.mac_pool/255,self.mac_pool%255)
    def __init__(self, node, label = ''):
        self.node=node
        netpylab.NetpylabObject.__init__(self, node.world, label)
        
        # self.world = node.world
        self.world.interfaces.append(self)
        
        self.handlers = []
        self.protocols = {}
        node.register_iface(self)
        self.mac = self.new_mac()

        
        self.status="down"
        self.channel = None
        self.world.log.debug(self.label +" attached_to "+ node.label)
        
        self.last_connection_time=0
        self.total_connection_time = 0
        self.times_connected = 0
        self.times_disconnected = 0
        #properties
        self.cost_per_byte_sent = 0
        self.cost_per_byte_received = 0
        self.cost_per_second = 0
        
        self.power_per_byte_sent = 0
        self.power_per_byte_received = 0
        self.power_per_second = 0
        
        #statistics
        self.packets_sent = 0
        self.packets_received = 0
        self.packets_lost = 0
        self.packets_dropped = 0
        
        self.data_sent = 0
        self.data_received = 0
        self.data_lost = 0
        self.data_dropped = 0
        
        self.byte_cost = 0
        self.byte_power = 0
        
        
    def start(self, at = 0):
        pass
        
    def register_handler(self, handler, protocol = None):
        self.handlers.append(handler)
        self.protocols[protocol] = handler
        
    @property
    def peers(self):
        if self.channel:
            return self.channel.interfaces
        else:
            return []
    
    def __len__(self):
        return len(self.label)
        
    @property
    def place(self):
                return self.node.place
    
    @property
    def position(self):
        return self.node.position
    
    def info(self):
        
        s = str(self) + '\n--- mac = ' + self.mac
        for handler in self.handlers:
            s += '\n' + handler.info()
        return s
        
            
    def update_after_connect(self, channel):
        self.last_connection_time = self.world.time
        self.times_connected += 1
        self.add_to_history('connected', str(channel))
        # self.world.log.info(self.label + " connected " + channel)
    
    def update_after_disconnect(self):
        self.total_connection_time += self.world.time - self.last_connection_time
        self.times_disconnected += 1
        self.node.disconnect_notification(self)
        self.add_to_history('disconnected')
        # self.world.log.info(self.label + " disconnected")
    
    def update_after_sending(self, p):
        size = p.size = len(p.data) 
        self.packets_sent += 1
        self.data_sent += size
        self.byte_cost += (size * self.cost_per_byte_sent)
        self.byte_power += (size * self.power_per_byte_sent)
        p.add_to_trip(self, 'broadcasted')
        self.world.log.debug(self.label + " packet_sent " + str(size))
    
    def update_after_receiving(self, p):
        size = p.size = len(p.data)  
        self.packets_received += 1
        self.data_received += size
        self.byte_cost += (size * self.cost_per_byte_received)
        self.byte_power += (size * self.power_per_byte_received)
        p.add_to_trip(self, 'received')
        self.world.log.debug(self.label + " packet_received " + str(size))
    
    def total_connection_time(self):
        if self.connected():
            return self.total_connection_time + (self.world.time - self.last_connection_time)
        else:
            return self.total_connection_time
    
    def cost(self):
        return self.byte_cost + self.total_connection_time() * self.cost_per_second
    
    def power(self):
        return self.byte_power + self.total_connection_time() * self.power_per_second
    
    def stop(self):
        self.world.log.info(self.label + " stopped")
    
    def send_ip(self, p, family='inet'):
        if family=='inet':
            self.arp.send(p)
        # if family == 'inet6':
        #     self.ICMPv6
        
    def scan(self):
        return
        
    def send(self, p, dest_iface=None):
        if not self.active:
            raise RuntimeError('Interface not active %s' %self.label)
        if not self.channel:
            raise RuntimeError('Interface not active : %s' % self.label)
        self.scan()
        try:
            p.size = len(p.data)
        except:
            raise RuntimeError('Malformed Packet %s ' % p)

        # if dest_iface:
        #     receiver_interfaces=[dest_iface]
        # else:
        #     receiver_interfaces = self.channel.interfaces
        # if not receiver_interfaces:
        #     return

        sent = False
        p = self.distorsion_model(p)
        delay = self.delay_model(p)
        for iface, is_reach in self.reachable.iteritems():
            if not is_reach or iface == self:
                continue
            sent = True
            netpylab.CallLater(self, delay, iface.receive, args=p)
            
        if sent:
            self.update_after_sending(p)
        else:
            p.add_to_trip(self, 'unreachable')
            
    def receive(self, p):
        self.update_after_receiving(p)
        if self.is_for_me(p):
            p.add_to_trip(self, 'accepted')
            self.dispatch(p)
        else:
            p.add_to_trip(self, 'refused', info = self.info())


    def packet_dst(self, p):
        return p.dst
        
    def is_for_me(self, p):
        return True
    
    def clean(self, p):
        return p, None
        
    def dispatch(self, p):
        p, info = self.clean(p)
        ptype = p.data.__class__
        try:
            handler = self.protocols[ptype]
        except KeyError:
            try:
                handler = self.protocols[None] # Bridge
            except KeyError:
                p.add_to_trip(self, 'not L2_dispatched', 'type : ' + str(ptype) + ' not in '+str(self.handlers))
                return
        p.add_to_trip(self, 'L2_dispatched')
        handler.receive(p, info)

    
    @property
    def proxied_mac_addresses(self):
        return [iface.mac for iface in self.node.wireless_iface.managed_ifaces]
            
    
    def is_reachable(self, other_iface):
        return True
    
    def delay_model(self, p):
        return 0.1 # Packets are delayed by 1 second
    
    def distorsion_model(self, p):
        return p # Do not modify the packet
    
    def connect(self, channel):
        if self.channel :
            raise RuntimeError('Already connected')
        self.channel = channel
        channel.register(self)
        for handler in self.handlers:
            handler.start()
        self.update_after_connect(channel)
        
    def disconnect(self):
        self.channel.unregister(self)
        self.channel = None
        for handler in self.handlers:
            handler.stop()

        self.update_after_disconnect()
    
    def ip(self, ip_addr, family='inet', prefix=None, alias=True):
        assert family in ['inet', 'inet6']
        if family == 'inet': addrs = self.ipv4_addresses
        elif family == 'inet6': addrs = self.ipv6_addresses
        if not prefix:
            prefix = 8
        index = self.has_ip(ip_addr)
        if index != -1:
            del(addrs[index])
        if alias:
            addrs.append((ip_addr, prefix))
        else:
            if index == 0:
                addrs.insert(0,(ip_addr, prefix))
            else:
                addrs[0]=(ip_addr, prefix)
            #Modify routing table
        self.node.resync(family)
    
    def del_ip(self, ip_addr, family='inet'):
        assert family in ['inet', 'inet6']
        if family == 'inet': addrs = self.ipv4_addresses
        elif family == 'inet6': addrs = self.ipv6_addresses
        
        index = self.has_ip(ip_addr, family)
        if index != -1:
            del(addrs[index])
        self.resync(family)
    
    def has_ip(self, ip_addr, family='inet'):
        assert family in ['inet', 'inet6']
        if family == 'inet': addrs = self.ipv4_addresses
        elif family == 'inet6': addrs = self.ipv6_addresses
        for i in range(len(addrs)):
            if addrs[i][0] == ip_addr:
                return i
        return -1

class RealInterface(Interface):
    def __init__(self, node, ifname):
        Interface.__init__(self, node)
        self.ifname = ifname
    
    def start(self, at=0, lifetime=None):
        Interface.start(self, at, lifetime)
        self.lifetime = lifetime
    
    def activate(self):
        Interface.activate(self)
        self.world.callInThread(sniff, store = False,
                                prn = self.receive,
                                timeout = self.lifetime,
                                iface = self.ifname)
    
    def receive(self, packet_data):
        #print p.summary()
        Interface.receive(self, (Packet(self, packet_data), None), "External Packet", "External")
    
    def send(self, p, dest_iface=None):
        send(p.data, iface = self.ifname)
    
    # def send(self, p, dest_iface=None):
    #     #print p.summary()
    #     receiver_interfaces = self.channel.interfaces
    #     
    #     if not receiver_interfaces:
    #         return
    #     p = self.distorsion_model(p)
    #     delay = self.delay_model(p)

    def deactivate(self):
        Interface.deactivate(self)

        

class Loopback(Interface):
    def __init__(self, node, label = ''):
        Interface.__init__(self, node, label = label)
        # self.node.rt6.route_add(ipv6.IPv6Address('::1'), self)
        # self.ip('127.0.0.1', prefix=8)

    def send(self, p):
        if not self.active:
            raise

        netpylab.CallLater(self, 0.001, self.receive, args=(p, self))
        self.update_after_sending(p)
            
    def receive(self, p):
        self.update_after_receiving(p)
        
        if self.is_for_me(p):
            p.add_to_trip(self, 'accepted')
            self.dispatch(p)
        else:
            p.add_to_trip(self, 'refused', info = self.info())

class EthernetInterface(Interface):
    color = (0.5,0.5,0.5)
    def __init__(self, node, label = '', channel = None):
        Interface.__init__(self, node, label)
        self.reachable = {}
        if channel :
            self.connect(channel)
            

    def is_for_me(self, p):
        dst = self.packet_dst(p)
        if dst in (self.mac, 'FF:FF:FF:FF:FF:FF'):
            return True
        for handler in self.handlers:
            if handler.is_for_me(dst):
                return True
            return False
            
    
    def send(self, p, dst_mac, src_mac = None):
        #d = dst_mac if dst_mac else self.mac
        src = src_mac if src_mac else self.mac
        p.add_at_bottom(l2.Ether(src=src, dst=dst_mac))
        Interface.send(self, p)

    def clean(self, p):
        info = {'src': p.src, 'dst': p.dst}
        p.remove_from_bottom()
        return p, info

class WirelessInterface(EthernetInterface):
    def __init__(self, node, label = '', range = 200, mode = 'managed'):
        self.range = range
        self.scan_interval = 0.5
        self.next_packet_send_time = 0
        assert mode in ('managed', 'master')
        if mode == 'managed':
            self.access_point = None
        elif mode == 'master':
            self.managed_ifaces = []
        self.mode = mode
        EthernetInterface.__init__(self, node, label, self.channel_class.channel)
        self.old_x = self.old_y = 0
        self.scan_thread = netpylab.Loop(self, self.scan_interval, self.scan)
        
        
        
    def send(self, p, dst_mac, src_mac = None):
        if self.mode == 'managed':
            if not self.access_point:
                return
            addr3 = self.access_point.mac
            # p.add_at_bottom(dot11.Dot11(addr1=src, addr2=dst_mac, addr3=
            #             self.access_point.mac) / l2.LLC() / l2.SNAP())
            # Interface.send(self, p)
        if self.mode == 'master':
            addr3 = self.mac
        
        src = src_mac if src_mac else self.mac
        p.add_at_bottom(dot11.Dot11(addr1=src, addr2=dst_mac, addr3=addr3) \
                            / l2.LLC() / l2.SNAP())
        Interface.send(self, p)
        

    def packet_dst(self, p):
        if self.mode == 'managed':
            return p.addr2
        elif self.mode == 'master':
            return p.addr3

    # def delay_model(self, p):
    #     data_rate = 100000 # octets/second
    #     injection_delay = len(p.data)/data_rate
    #     time = self.world.time
    #     d = max(0, self.next_packet_send_time - time) + injection_delay
    #     self.next_packet_send_time = max(time, self.next_packet_send_time) + injection_delay
    #     return d
        
    def clean(self, p):
        info = {'addr1': p.addr1, 'addr2': p.addr2, 'addr3': p.addr3}
        p.remove_from_bottom(3)
        return p, info

    def is_reachable(self, other_iface):
        d = self.position.get_distance(other_iface.position)
        return d < self.range

    def scan(self):
        pos = self.position
        if pos.x == self.old_x and pos.y == self.old_y:
            return

        for iface in self.channel.interfaces:
            self.reachable[iface] = self.is_reachable(iface)
            iface.reachable[self] = iface.is_reachable(self)
        
        for iface, is_reach in self.reachable.iteritems():
            if not is_reach:
                if self.mode == 'managed' and iface == self.access_point:
                    self.disconnect_from_ap()
                if self.mode == 'master' and iface.mode == 'managed' and self == iface.access_point:
                    iface.disconnect_from_ap()
            else:
                if self.mode == 'managed' and self.access_point == None and iface.mode == 'master':
                    self.connect_to_ap(iface)
    
    def connect_to_ap(self, ap):
        self.access_point = ap
        ap.managed_ifaces.append(self)

    def disconnect_from_ap(self):
        self.access_point.managed_ifaces.remove(self)
        self.access_point = None

    @property
    def peers(self):
        if self.mode == 'managed':
            if self.access_point:
                return [self.access_point]
            else:
                return []
        elif self.mode == 'master':
            return self.managed_ifaces
        else:
            assert False

class WiFiInterface(WirelessInterface):
    color = (0,0,1)
    channel_class = channels.WiFiChannel
    def __init__(self, node, label = '', range =200, mode = 'managed'):
        WirelessInterface.__init__(self, node, label, range, mode)
    
class WiMaxInterface(WirelessInterface):
    color = (0,1,0)
    channel_class = channels.WiMaxChannel
    def __init__(self, node, label = '', range =3000, mode = 'managed'):
        WirelessInterface.__init__(self, node, label, range, mode)

class MobileIPv6Tunnel(Interface):
    color = (0.8, 0.1, 0.5)
    def __init__(self, node, top_addr, tun_addr, tun_peer_addr, label = '', iface = None):
        Interface.__init__(self, node, label)
        self.tun_addr = tun_addr
        self.tun_peer_addr = tun_peer_addr
        self.iface = iface
        if top_addr:
            self.ipv6.addresses.register(top_addr)

    def send(self, p):
        p.add_at_bottom( inet6.IPv6(dst=str(self.tun_peer_addr), src=str(self.tun_addr)) )
        p.add_to_trip(self.node, 'tunneled')
        self.node.route_ipv6_old(p)

            
    # def receive(self, p):
    #     # p.data = p[inet6.IPv6].payload
    #     # p.remove_from_bottom()
    #     self.node.dispatch(inet6.IPv6, p, self)

    # @property
    # def addresses(self):
    #     return (self.addr)
    
    # @addresses.setter
    # def addresses(self, val):
    #     raise
    
    



# class TunTapInterface(SimpleInterface):
#
#     def connect(self, tun_tap_ap):
#         SimpleInterface.connect(self, tun_tap_ap)
#         os.system("ifconfig "+ tun_tap_ap.interface() +" up")
#         if sys.platform == "darwin":
#             os.system("ifconfig "+ tun_tap_ap.interface() +" inet6 "+ tun_tap_ap.network().ipv6_prefix() + "%X" % self.node().unique_id()+"/64")
#         else:
#             os.system("ifconfig "+ tun_tap_ap.interface() +" add " + tun_tap_ap.network().ipv6_prefix() + "%X" % self.node().unique_id()+"/64")
#
#     def file(self):
#         if self.access_point():
#             return self.access_point().file()
#
#     def pull_packet(self):
#         select([self.file()],[],[])[0][0]
#         packet = IPv6Packet(os.read(self.file(),1500))
#         if not packet.is_ipv6():
#             raise TypeError, "Non IPv6 Packet Received"
#         return packet, self.access_point()
#

#
