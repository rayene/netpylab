import layers.ipv6
import scapy.layers.inet as inet, scapy.layers.inet6 as inet6

from netpylab import NetpylabObject
# from packets import Packet
# import places
#import vwidgets
import interfaces

class Node(NetpylabObject):
    def __init__(self, place, label = '', autostart_apps = True, autostart_ifaces = True) :
        """Hello, this is the doc for the Node Class"""
        self.place = place
        NetpylabObject.__init__(self, place.world, label)
        
        self.autostart_apps = autostart_apps
        self.autostart_ifaces = autostart_ifaces
        self.place.attach_node(self)
        self.applications = []
        #self.interfaces = [self.loopback]
        self.interfaces=[]
        self.routing_table={}
        self.active = False
        # self.world = self.place.world
        self.world.nodes.append(self)
        
    
    def register_iface(self, iface):
        self.interfaces.append(iface)
        
    def start(self, at=0):
        if self.autostart_ifaces:
            for iface in self.interfaces: iface.start(at)
        if self.autostart_apps:
            for app in self.applications: app.start(at)

    def stop(self, at=0):
        for iface in self.interfaces: iface.stop(at)
        for app in self.applications: app.stop(at)
        NetpylabObject.stop(self, at)

    def attach_to(self, place):
        self.place = place
        place.attach_node(self)
        self.world.log.debug(self.label + "attached_to "+ place.label)
        
    
    @property
    def position(self):
        return self.place.position

    def info_applications(self, level):
        return "".join(a.info(level) for a in self.applications)        

    def info_interfaces(self, level):
        return "".join(i.info(level) for i in self.interfaces)

    def info(self, level=0):
        return level * "---"+ self.label + ":\n" + (level+1) * "---"+"Applications :\n" +  self.info_applications(level+2)  + (level+1) * "---"+"Interfaces :\n" + self.info_interfaces(level+2)

    def print_info(self):
        print self.info(0)

class Bridge(object):

    def start(self):
        pass

    def stop(self):
        pass
    
    def is_for_me(self, dst):
        return dst in self.peer.wireless_iface.proxied_mac_addresses or '33:33:' in dst
        
    def receive(self, p, info):
        dst = info['dst']
        src = info['src']
        # p.remove_from_bottom()
        if '33:33' in dst or dst in [iface.mac for iface in self.peer.wireless_iface.managed_ifaces]:
                p.add_to_trip(self.ethernet_iface, 'bridged')
                self.peer.wireless_iface.send(p, dst, src)
                return
        p.add_to_trip(self.ethernet_iface, 'not bridged')
    
    def info(self):
        return 'Bridge'
        

class WirelessBridge(Bridge):

    def is_for_me(self, dst):
        return True

    def receive(self, p, info):
        dst = info['addr2']
        src = info['addr1']
        p.add_to_trip(self.wireless_iface, 'bridged')
        self.peer.ethernet_iface.send(p, dst, src)


class AccessPoint(Node):
    suffix = '_'
    def __init__(self, place, label = '', wireless_iface = interfaces.WiFiInterface, channel = None):
        Node.__init__(self, place, label)
        self.bridge = Bridge()
        self.wbridge = WirelessBridge()
        self.bridge.peer = self.wbridge
        self.wbridge.peer = self.bridge
        self.ethernet_iface = interfaces.EthernetInterface(self, label = self.label + '_eth', channel = channel)
        self.ethernet_iface.register_handler(self.bridge)
        self.wireless_iface = wireless_iface(self, mode = 'master', label = self.label + self.__class__.suffix)
        self.wireless_iface.register_handler(self.wbridge)
        self.wbridge.wireless_iface = self.wireless_iface
        self.bridge.ethernet_iface = self.ethernet_iface

        
class WiFiAccessPoint(AccessPoint):
    suffix = '_wifi'
    pass
    
class WiMaxAccessPoint(AccessPoint):
    suffix = '_wimax'
    def __init__(self, place, label ='', channel = None):
        AccessPoint.__init__(self, place, label, interfaces.WiMaxInterface, channel)
    
class IPNode(Node):
    def __init__(self, place, label = '', autostart_apps = True, autostart_ifaces = True):
        Node.__init__(self, place, label, autostart_apps, autostart_ifaces)
        #self.rt4 = ipv4.Route4(self)
        self.rt6 = layers.ipv6.Route6(self)
        self.forwarding = False
        self.loopback = interfaces.Loopback(self)
        self.ports = {
                        inet.IP :{inet.UDP:{}, inet.TCP:{}}, 
                        inet6.IPv6:{inet.UDP:{}, inet.TCP:{}}
                    }
        self.dispatcher = {
                            inet.IP :{   
                                inet.UDP: self.handle_ip_udp, 
                                inet.TCP:self.handle_ip_tcp
                                }, 
                            inet6.IPv6:{
                                inet.UDP:self.handle_ipv6_udp, 
                                inet.TCP:self.handle_ipv6_tcp,
                                inet6.ICMPv6ND_RA: self.handle_ipv6_icmpv6ra,
                                inet6.ICMPv6ND_RS: self.handle_ipv6_icmpv6rs, 
                                inet6.ICMPv6ND_NS: self.handle_ipv6_icmpv6ns,
                                inet6.ICMPv6ND_NA: self.handle_ipv6_icmpv6na,
                                }
                        }
    def register_iface(self, iface):
        iface.ipv6 = layers.ipv6.IPv6(iface)
        Node.register_iface(self, iface)
        iface.register_handler(iface.ipv6, inet6.IPv6)

    def route_ipv4(self, packet, iface=None):
        if not iface:
            #packet.route = self.rt4.route
            dst = self.rt4.route(packet.dst)
            if dst:
                if type(dst)=='str': # no route to host
                    self.world.log.info('No route to host ' + packet.dst)
                    return
                iface = dst[0]
            iface.send_ip(packet, family=inet.IP)
    
    def route_ipv6(self, packet, iface=None):
        dst = layers.ipv6.IPv6Addr(packet[inet6.IPv6].dst, iface = iface)
        route = self.rt6.route(dst)
        if route:
            packet.add_to_trip(self, 'routed', info = 'route = ' + str(route))
            if route.__class__ == layers.ipv6.NeighborCacheEntry:
                route.iface.ipv6.send(packet, route)
            elif issubclass(route.__class__ , interfaces.Interface):
                # print packet.summary()
                # print route 
                # print route.ipv6.addresses
                if dst in route.ipv6.addresses:
                    self.dispatch(inet6.IPv6, packet, iface)
                    # print self, route, route.ipv6.addresses
                elif route.ipv6.has_icmpv6:
                    nce = route.ipv6.icmpv6.create_neighbor(str(dst))
                    route.ipv6.send(packet, nce)
                else:
                    # print self, route, packet.description, route.ipv6.addresses
                    # print 'FFFFFFFFFFFFFFFF', self.label, dst, route, route.ipv6.addresses
                    route.ipv6.send(packet, route)
            else:
                packet.add_to_trip(self, 'not routed', 'partial route')
                #print route
                raise # should never happen
        # for iface in self.interfaces:
        #     if dst in iface.ipv6_addresses:
        #         print "TODO: Weird Situation"
        #         packet.add_to_trip(self, 'weird')
        else:
            packet.add_to_trip(self, 'not routed', 'no route at all' + str(self.rt6))
    
    def which_ipv6_src_address(self, dst_addr, iface=None):
        dst = layers.ipv6.IPv6Addr(dst_addr, iface) #TODO: Replace dst by src
        if dst.is_linklocal:
            print dst
            assert iface
            return iface.ipv6.linklocal_addr
        elif dst.is_global:
            if iface:
                ifaces = [iface]
            else:
                ifaces = self.interfaces
            for iface in ifaces:
                try:
                    return iface.ipv6.addresses.globals()[0]
                except IndexError:
                    continue
            assert False
            return None
        else:
            assert False
            return None

    def resync(self, family= inet.IP):
        assert family in [inet.IP, inet6.IPv6]
        if family == inet.IP   : self.rt4.resync()
        elif family == inet6.IPv6: self.rt6.resync()

    def register(self, receive_func, ip_family = inet.IP, proto=inet.TCP, port=None):
        ports = self.ports[ip_family][proto]
        if port:
            if not ports.has_key(port):
                ports[port]=receive_func
                return port
            else:
                return False
        for i in xrange(1024,3000):
            if not ports.has_key(i):
                ports[i]=receive_func
                return i
        return False

    def unregister(self, ip_family = inet.IP, proto=inet.TCP, port=None):
        del(self.ports[ip_family][proto][port])
    
    def handle_ip_udp(self, p, iface):
        self.handle_tcp_udp(p, inet.IP, inet.UDP)
        
    def handle_ip_tcp(self, p, iface):
        self.handle_tcp_udp(p, inet.IP, inet.TCP)
        
    def handle_ipv6_udp(self, p, iface):
        self.handle_tcp_udp(p, inet6.IPv6, inet.UDP)
        
    def handle_ipv6_tcp(self, p, iface):
        self.handle_tcp_udp(p, inet6.IPv6, inet.TCP)

    def handle_tcp_udp(self, p, ip_family, proto):
        if self.ports[ip_family][proto].has_key(p.dport):
            p.add_to_trip(self, 'L4_dispatched')
            socket = self.ports[ip_family][proto][p.dport]
            socket.receive(p)
        else:
            p.add_to_trip(self, 
                    'not L4_dispatched', 
                    'port %d not open, open ports : %s' % (p.dport, str(self.ports[ip_family][proto].keys())))
        
    def handle_ipv6_icmpv6ra(self, p, iface):
        iface.ipv6.icmpv6.receive_router_advertisement(p)
    def handle_ipv6_icmpv6rs(self, p, iface):
        iface.ipv6.icmpv6.receive_router_solicitation(p)
    def handle_ipv6_icmpv6ns(self, p, iface):
        iface.ipv6.icmpv6.receive_neighbor_solicitation(p)
    def handle_ipv6_icmpv6na(self, p, iface):
        iface.ipv6.icmpv6.receive_neighbor_advertisement(p)


    def dispatch(self, ip_family, packet, iface):
        ptype = packet[inet6.IPv6].payload.__class__
        try:
            reception_handler = self.dispatcher[ip_family][ptype]
        except KeyError:
            packet.add_to_trip(self, 'not L3_dispatched', str(ptype) + ' not in ' + str(self.dispatcher[ip_family].keys()))
            self.world.log.warning(self.label + ' did not dispatch ' + str(ptype) + ' not in ' + str(self.dispatcher[ip_family].keys()))
            return
        packet.add_to_trip(self, 'L3_dispatched')
        reception_handler(packet, iface)

    #     
    # def dispatch(self, ip_family, packet, iface):
    #     ptype = packet[ip_family].payload.__class__
    #     if ptype in self.dispatcher[ip_family]:
    #         reception_handler = self.dispatcher[ip_family][ptype]
    #         reception_handler(packet, iface)
    #     else:
    #         packet.add_to_trip('not dispatched', str(ptype) + ' not in ' + self.dispatcher[ip_family])
    #         self.world.log.warning(self.label + ' did not dispatch ' + str(ptype))
    
    def global_ipv6_notification(self, iface, addr):
        pass
    def disconnect_notification(self, iface):
        pass

class IPRouter(IPNode):
    def __init__(self, place, label='' ):
        IPNode.__init__(self, place, label)
        self.forwarding = True


class MobileNode(IPNode):
    def __init__(self, place, HoA, HA_addr, home_prefix, prefix_len = 64, label = '', autostart_apps = True, autostart_ifaces = True):
        IPNode.__init__(self, place, label, autostart_apps, autostart_ifaces)
        self.mobileipv6 = layers.ipv6.MobileIPv6(self, HA_addr, home_prefix, prefix_len)
        self.HoA = layers.ipv6.IPv6Addr(HoA)
        self.HA_addr = layers.ipv6.IPv6Addr(HA_addr)
        # self.dispatcher[inet6.IPv6][inet6.MIP6MH_BA] = self.mobileipv6.handle_ipv6_binding_acknowledgement
        self.dispatcher[inet6.IPv6][inet6.IPv6ExtHdrRouting] = self.mobileipv6.handle_ipv6_binding_acknowledgement
        self.dispatcher[inet6.IPv6][inet6.IPv6] = self.mobileipv6.handle_ipv6_ipv6

    def global_ipv6_notification(self, iface, addr):
        self.mobileipv6.global_ipv6_notification(iface, addr)
    
    def disconnect_notification(self, iface):
        self.mobileipv6.disconnect_notification(iface)
    #         
    # def disconnect_notification(self, iface):
    #         tun = self.deactivate_tunnel(iface)
    #         if tun == self.current_tunnel:
    #             for iface in self.interfaces:
    #                 if iface.__class__ == interfaces.MobileIPv6Tunnel and iface.active:
    #                     self.current_tunnel = iface
    #                     self.send_binding_update(iface.iface)
    #                 else:
    #                     self.current_tunnel = None
                        
    def which_ipv6_src_address(self, dst_addr, iface=None):
        return self.HoA
    
    def which_ipv6_src_address_old(self, dst_addr, iface=None):
        return IPNode.which_ipv6_src_address(self, dst_addr, iface)        
    
    def route_ipv6(self, packet, iface=None):
        tunnels = self.tunnels()
        if len(tunnels):
            tun = tunnels[0]
            packet.add_to_trip(self, 'tunneled', tun.label)
            tun.send(packet)
            return
        packet.add_to_trip(self, 'not tunneled')

    def route_ipv6_old(self, packet, iface=None):
        return IPNode.route_ipv6(self, packet, iface)
    

    def tunnels(self):
        return filter(lambda iface: iface.__class__ == interfaces.MobileIPv6Tunnel, self.interfaces)
    
    # def handle_ipv6_ipv6(self, packet, iface):
    #     #packet.data = packet[inet6.IPv6].payload
    #     packet.add_to_trip(self, 'detunneled')
    #     self.tunnels[iface].receive(packet)

    # def handle_ipv6_binding_acknowledgement(self, packet, iface):
    #     #TODO: R Check packet correctness
    #     # First verify the HA_addr
    #     src = packet[inet6.IPv6].src
    #     if src == self.HA_addr:
    #         self.is_associated =True
    #     else:
    #         # The HA_addr did not correpond with the node which answer to our BU 
    #         raise

class MobileNodeMCoA(MobileNode):
    # def __init__(self, place, HoA, HA_addr, label = '', autostart_apps = False, autostart_ifaces = True):
    #     MobileNode.__init__(self, place, HoA, HA_addr, label, autostart_apps, autostart_ifaces)
        
    # def global_ipv6_notification(self, iface, addr):
    #     self.create_or_activate_tunnel(iface, addr)
    #     self.send_binding_update(iface)

    def disconnect_notification(self, iface):
        tun = self.deactivate_tunnel(iface)

    def route_ipv6(self, packet, iface=None):
        for i, t in self.tunnels.iteritems():
            if self.world.scenario ==1:
                if t.active: #i.__class__ == interfaces.WiFiManaged
                    packet.add_to_trip(self, 'tunneled', t.label)
                    t.send(packet, str(self.HA_addr))
                    return
            else:
                if t.active:
                    if i.__class__ == interfaces.WiFiManaged:
                        packet.add_to_trip(self, 'tunneled', t.label)
                        t.send(packet, str(self.HA_addr))
                        if self.a:
                            self.world.wf1.data_size = 1280
                            self.a = False
                            if not self.s:
                                self.world.wf2.start()
                                self.s = True
                        return
                    else:
                        if self.a == False:
                            # try:
                            #     self.world.wf2.stop()
                            # except:
                            #     pass
                            self.a = True
                        self.world.wf1.data_size = 640
                        packet.add_to_trip(self, 'tunneled', t.label)
                        t.send(packet, str(self.HA_addr))
                        return

                            
            # elif i.__class__ == interfaces.WiMaxManaged and t.active:
            #     packet.add_to_trip(self, 'tunneled', t.label)
            #     packet[inet.UDP] = 
            #     t.send(packet, str(self.HA_addr))
            #     return
                
        packet.add_to_trip(self, 'not tunneled')

class HomeAgent(IPRouter):
    def __init__(self, place, HA_addr ,home_prefix, prefix_len = 64, label='' ):
        IPRouter.__init__(self, place, label)
        self.HA_addr = HA_addr
        self.mobileipv6 = layers.ipv6.MobileIPv6(self, HA_addr ,home_prefix, prefix_len)
        self.dispatcher[inet6.IPv6][inet6.IPv6] = self.mobileipv6.handle_ipv6_ipv6
        # self.dispatcher[inet6.IPv6][inet6.MIP6MH_BU] = self.mobileipv6.handle_ipv6_binding_update
        self.dispatcher[inet6.IPv6][inet6.IPv6ExtHdrDestOpt] = self.mobileipv6.handle_ipv6_binding_update
        self.loopback.ipv6.addresses.register(HA_addr)

    def register_iface(self, iface):
        Node.register_iface(self, iface)
        has_icmp = (iface.__class__ == interfaces.EthernetInterface)
        iface.ipv6 = layers.ipv6.IPv6(iface, has_icmp)
        iface.register_handler(iface.ipv6, inet6.IPv6)

    # def send(self, p):
    #     dst_ip = p[inet6.IPv6].dst
    #     if dst_ip == self.HA_addr:
    #         nh = p[inet6.IPv6].payload.__class__
    #         if nh == inet6.IPv6:
    #             self.handle_ipv6_ipv6(p, None)
    #         elif nh == inet6.MIP6MH_BU:
    #             self.handle_ipv6_binding_update(p,None)
    #         else:
    #             #print nh, p
    #             raise
    #     else:
    #         self.send_data_packet(p)

    # def send_data_packet(self, p):
    #     HoA = layers.ipv6.IPv6Addr(p[inet6.IPv6].dst)
    #     for hoa_bc in self.binding_cache.keys():
    #         if hoa_bc == HoA: # in self.binding_cache:
    #             CoA = self.get_coa(hoa_bc)
    #             if CoA:
    #                 p.add_to_trip(self, 'tunneled')
    #                 p.add_on_top(inet6.IPv6(src=str(self.HA_addr), dst = str(CoA)))
    #                 self.route_ipv6(p)
    #                 return
    #     print 'NO Tunnel associated to', HoA, type(HoA), self.binding_cache

    def get_coa(self, hoa_bc):
        return self.binding_cache[hoa_bc]

    def route_ipv6_old(self, packet, iface=None):
        return IPRouter.route_ipv6(self, packet, iface)
        
class HomeAgentMCoA(HomeAgent):

    def get_coa(self, hoa_bc):
        for i, t in self.binding_cache[hoa_bc].iteritems():
            if i.__class__ == interfaces.WiFiManaged:
                return t.global_ipv6
        
    #         
    # def handle_ipv6_binding_update(self, packet, iface = None):
    #     print 'HAAAHZEIAZHAIZHEPI'
    #     layers.ipv6.IPv6Addr(packet[inet6.IPv6].src)
    #     HoA = layers.ipv6.IPv6Addr(packet[inet6.HAO].hoa)
    #     for hoa_bc in self.binding_cache.keys():
    #         if hoa_bc == HoA: # in self.binding_cache:
    #             self.binding_cache[hoa_bc] = packet.tunnels
    #     self.binding_cache[HoA] = packet.tunnels
    #     self.send_binding_acknowledgement('2001::1')

class MobileRouter(IPRouter):
    def __init__(self, place, x=0, y=0):
        IPRouter.__init__(self, place)
    

class RemoraMobileRouter_step1(MobileRouter):
    def __init__(self, place, x=0, y=0):
        MobileRouter.__init__(self, place, x=0, y=0)
        # self.admin = Administrator(self)
        # self.env=Environment(self)
        self.mrp = []
        self.network_list = {"orange-umts": None }
        self.flow_list = []
        
    def flow_list(self):
        return self.flow_list
    def add_flow(self, flow):
        self.flow_list.append(flow)

    def which_tunnel(self, packet):
        mapping={"udp-cbr": ["Wifi", "Umts"],
                "icmpv6" : ["Umts"],
                "ssh" : ["Umts"],
                "unknown" : ["Wifi"]
                }
        
        flow = None
        for f in self.flow_list():
            if f.is_my_packet(packet):
                flow = f
        
        # if flow == None:
        #     flow = Flow(packet)
        #     self.add_flow(flow)
            
        
        if mapping.has_key(flow.type()):
            for techno in mapping[flow.type()]:
                for iface in self.interfaces:
                    if iface.technology() == techno:
                        return iface
        return None # drop packet


class BasicNode(IPNode):
    def __init__(self, place):
        IPNode.__init__(self, place)
        self.applications=[]
        self.interfaces=[]
        #default_router_interface.config_peer_iface(self)
    
    def application(self):
        return self.applications()[0]
    def flow(self):
        return self.application().flows()[0]
    def interface(self):
        return self.interfaces[0]
    def ipv6_address(self):
        return self.interface()._ipv6addresses[0]
    def ipv6_prefix(self):
        return self.interface().ipv6_prefix()
    def start_flow(self):
        self.flow().start()
    def stop_flow(self):
        self.flow().stop()
        
    #def direct_connect_to(self, other_node):
    #    i_self = DirectConnectionInterface("direct_if_to_"+other_node.label, self)
    #    i_other = DirectConnectionInterface("direct_if_to_" + self.label + other_node)    
    
class MobileNetworkNode(BasicNode):
    pass
    #def __init__(self, default_router_interface):
    #    BasicNode.__init__(self, default_router_interface)
        ##self.applications=[]
        #self.interfaces=[]

    
class CorrespondentNode(BasicNode):
#    def __init__(self, default_router_interface):
#        BasicNode.__init__(self, default_router_interface)
    pass

class Layer2Node(Node):
    def __init__(self, place ):
        Node.__init__(self, place)
        
class EthernetSwitch(Layer2Node):
    
    def __init__(self, router, network):
        Layer2Node.__init__(self, router, network)
        
# class AccessPoint(Layer2Node):
#     def __init__(self, router, network):
#         Layer2Node.__init__(self, place)
#         self.connect(network)
#         self.connected_interfaces = []
#         self.world.log.info(self.label + "connected " + network.label)
#         self.q = Queue(100)
#     def network(self):
#         return self.network
#     #         return True
#     #     else:
#     #         return False
#     def connect(self, network):
#         self.network = network
#         Interface.connect(self, network)
#         network.add_access_point(self)
#     def add_connected_interface(self,interface):
#         self.connected_interfaces.append(interface)
#     def connected_interfaces(self):
#         return self.connected_interfaces
#     def remove_connected_interface(self, interface):
#         self.connected_interfaces.remove(interface)
# 
# class EmulatedAccessPoint(AccessPoint):
#     def __init__(self, router, network):
#         AccessPoint.__init__(self, router, network)
#         self.q = queue.Queue(100)
# 
# class EthernetSwitch(EmulatedAccessPoint):
#     def __init__(self, router, network):
#         AccessPoint.__init__(self, router, network)
# 
# class WirelessAccessPoint(EmulatedAccessPoint):
#     def __init__(self, router, network, delta_x=0, delta_y=0):
#         AccessPoint.__init__(self, router, network)
#         self.delta_x = delta_x # (m)
#         self.delta_y = delta_y # (m)
# 
#     def move(self, x,y):
#         nx, ny = self.node().position()
#         self.delta_x = x - nx
#         self.delta_y = y - ny
#         self.world.log.info(self.label + "moved " + str(x) +" "+str(y))
#         
#     def position(self):
#         nx, ny = self.node().position()
#         return nx+self.delta_x, ny+self.delta_y 
#     
#     def Range(self):
#         return self.range
# 
# class WifiAccessPoint(WirelessAccessPoint):
#     def __init__(self, router, network, delta_x=0, delta_y=0):
#         WirelessAccessPoint.__init__(self, router,network, delta_x, delta_y)
#     def Range(self):
#         return 500
# 
# class UmtsAntenna(WirelessAccessPoint):
#     def __init__(self, router, network, delta_x=0, delta_y=0):
#         WirelessAccessPoint.__init__(self, router,network, delta_x, delta_y)
#     def Range(self):
#         return 2000
# class WimaxAccessPoint(WirelessAccessPoint):
#     def __init__(self, router, network, delta_x=0, delta_y=0):
#         WirelessAccessPoint.__init__(self, router,network, delta_x, delta_y)
#     def Range(self):
#         return 100
#  
# class TunTapAccessPoint(AccessPoint):
#     def __init__(self, router, network):
#         AccessPoint.__init__(self, router, network)
#         IFF_TUN   = 0x0001
#         IFF_TAP   = 0x0002
#         IFF_NO_PI = 0x1000
#         TUNMODE = IFF_TUN 
#         TUNSETIFF = 0x400454ca
#         if sys.platform == "darwin":
#             file_path = "/dev/tun" + str(self.node().unique_id())
#             self.file = os.open(file_path, os.O_RDWR)
#             self.interface ="tun"+ str(self.node().unique_id())
#         else:
#             file_path = "/dev/net/tun"    
#             self.file = os.open(file_path, os.O_RDWR)
#             self.ifs = ioctl(self.file, TUNSETIFF, struct.pack("16sH", "iface%d", TUNMODE))
#             self.interface = self.ifs[:16].strip("\x00")
# 
#     def interface(self):
#         return self.interface
# 
#     def file(self):
#         return self.file
# 
#     def push_packet(self, packet):
#         os.write (self.file(), packet.data())
# 
#     def run(self):
#         pass
