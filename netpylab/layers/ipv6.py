#!/usr/bin/env python
# encoding: utf-8
"""
ipv6.py

Created by Rayene on 2009-03-06.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""
from scapy.layers import inet, inet6, l2
import scapy.utils6 as utils6
import socket
from netpylab import CallLater
from packets import Packet
import interfaces
import nodes

class IPv6(object):
    def __init__(self, iface, has_icmpv6 = True):
        self.iface = iface
        self.world = iface.world
        self.node = iface.node
        self.addresses = IPv6Addresses(self.iface)
        self.mcast_mac_addresses = []
        self._linklocal_addr = None
        self.manual_addresses = []
        self.manual_routes = []
        self.has_icmpv6 = has_icmpv6
        if has_icmpv6:            
            if self.node.forwarding:
                self.icmpv6 = ICMPv64Router(self)
            else:
                self.icmpv6 = ICMPv64Host(self)
    
    def start(self):
        if self.has_icmpv6:
            self.icmpv6.start()

    def stop(self):
        if self.has_icmpv6:
            self.icmpv6.reset()
        
    def register_mac_mcast(self, mac):
        if mac in self.mcast_mac_addresses:
            self.world.log.warning(self.iface.label + ".ipv6 : multicast mac address already registred")
        else:
            self.mcast_mac_addresses.append(mac)
    
    def unregister_mac_mcast(self, mac):
        try:
            self.mcast_addresses.remove(mac)
        except:
            self.world.log.warning(self.iface.label + ".ipv6 : multicast mac address not registred")

    def is_for_me(self,dst):
        return dst in self.mcast_mac_addresses
    
    def receive(self, p, info):
        addr = IPv6Addr(p[inet6.IPv6].dst, iface = self.iface)
        if addr in self.addresses:
            self.node.dispatch(inet6.IPv6, p, self.iface)
        elif self.node.forwarding and not addr.is_linklocal and not addr.is_multicast:
            self.node.route_ipv6(p)
        else:
            p.add_to_trip(self.iface, 'deleted', 'not in IPv6 addresses and not routable' + str(self.addresses))

    def send(self, p, neighbor):
        if neighbor.__class__ == NeighborCacheEntry:
            self.icmpv6.send(p, neighbor)
        else:
            neighbor.send(p)

    def info(self):
        s = '--- IPv6 mcast mac adresses = ' + str(self.mcast_mac_addresses)
        s +='\n--- IPv6 link local = ' + str(self.linklocal_addr) 
        s +='\n--- IPv6 = ' + str(self.addresses)
        return s

    def manual_route_add(self, prefix_or_addr, iface, prefixlen, next_hop):
        self.manual_routes.append((prefix_or_addr, iface, prefixlen, next_hop))
        # self.iface.add_to_history('IPv6 added manual route', prefix_or_addr + '/'+ str(prefixlen)+'%' + str(iface)  + ' -----> '+ next_hop)
    
    def get_linklocal_addr(self):
        return self._linklocal_addr
    
    
    def set_linklocal_addr(self, addr):
        self._linklocal_addr = addr
        # self.iface.add_to_history('IPv6 configured a link local address', str(addr))
        if not addr:
            raise
        for (prefix_or_addr, iface, prefixlen, next_hop) in self.manual_routes:
            nce = iface.ipv6.icmpv6.create_neighbor(next_hop)
            # TODO: check if on_link or not
            dst = IPv6Prefix(prefix_or_addr, 
                            prefixlen = prefixlen,
                            author = self.iface,
                            OnLinkFlag = False,
                            next_hop = nce)
            self.node.rt6.route_add(dst)
    linklocal_addr = property(get_linklocal_addr, set_linklocal_addr)
    
class AddressList(list):

    def __init__(self, creator):
        list.__init__(self)
        self.creator = creator

    def flush(self, author = None):
        if not author :
            del self[:]
        else:
            deleted = 0
            for i in range(len(self)):
                if self[i-deleted].author == author:
                        del self[i-deleted]
                        deleted +=1

class IPv6Prefix(object):
    def __init__(self, addr, prefixlen, iface=None, next_hop = None, author = None, OnLinkFlag = True, AutonomousFlag = True ):
        self.prefixlen = prefixlen
        self.addr = addr
        self.iface = iface
        if iface and not issubclass(iface.__class__, interfaces.Interface):
            raise AttributeError(iface, 'is not an interface !') 
        self.next_hop = next_hop
        self.OnLinkFlag = OnLinkFlag
        self.AutonomousFlag = AutonomousFlag
        self.author = author
        
        if len(addr) != 16:
            #TODO: correct this !
            self.addr = socket.inet_pton(socket.AF_INET6, self.addr)
        
    def __cmp__(self, other):
        return cmp(other.prefixlen, self.prefixlen)
    
    @property
    def is_prefix(self):
        return self.prefixlen < 128
    
    def __contains__(self, dst_ip):
        mask = utils6.in6_cidr2mask(self.prefixlen)
        return self.addr == utils6.in6_and(dst_ip.addr, mask)
            
            #return (self.is_linklocal and self.iface == dst_ip.iface) or \
            #        not self.is_linklocal
    def __repr__(self):
        return self.__str__()
        
    def __str__(self):
        pfx = ifc = next_hop =''
        if self.prefixlen < 128:
            pfx = '/'+str(self.prefixlen)
        if self.iface:
            ifc = '%'+self.iface.label
        if self.next_hop:
            next_hop = ' => ' + str(self.next_hop)
        return socket.inet_ntop(socket.AF_INET6, self.addr)+pfx+ifc+next_hop

    def __eq__(self, other):
        if type(other) == str:
            other = IPv6Prefix(other)
        if other.iface and self.iface and other.iface <> self.iface:
            return False    
        return other.prefixlen == self.prefixlen and other.addr == self.addr 
        
        # if self.addr == other.addr and self.prefixlen == other.prefixlen :
        #     return (self.is_linklocal and self.iface == other.iface) or \
        #             not self.is_linklocal
                

    def mac2ip(self, mac):
        return IPv6Addr(socket.inet_ntop(socket.AF_INET6, self.addr) + \
            utils6.in6_mactoifaceid(mac))

    @property
    def is_global(self):
        return self in IPv6Prefix('2000::', 3)
        
    @property
    def is_linklocal(self):
        return self in IPv6Prefix('fe80::', 10)

    @property    
    def is_sitelocal(self):
        return self in IPv6Prefix('fec0::', 10)
    
    @property    
    def is_multicast(self):
        return self in IPv6Prefix('ff00::', 8)

    @property
    def is_loopback(self):
        return self in IPv6Prefix('::1', 128)

    @property
    def scope(self):
        if self.is_global:          return utils6.IPV6_ADDR_GLOBAL
        elif self.is_linklocal:     return utils6.IPV6_ADDR_LINKLOCAL
        elif self.is_sitelocal:    return utils6.IPV6_ADDR_SITELOCAL
        elif self.is_multicast:     return utils6.IPV6_ADDR_MULTICAST
        elif self.is_loopback:      return utils6.IPV6_ADDR_LOOPBACK
        else:
            raise AttributeError("Unknown address")
    
class Route6(AddressList):
    
    def route(self, dst_ip):
        "RFC 2461 page 34"
        #scope = dst_ip.scope
        for route in self:
            if dst_ip in route:
                if route.__class__ == NeighborCacheEntry:
                    return route
                if route.__class__ == MobileIPv6CacheEntry:
                    return route
                if route.__class__ in (IPv6Prefix, IPv6Addr):
                    if route.next_hop.__class__ in (IPv6Addr, IPv6Prefix, NeighborCacheEntry):
                        # print route, route.__class__.__name__
                        return self.route(route.next_hop)
                    if issubclass(route.next_hop.__class__, interfaces.Interface):
                        return route.next_hop
                    else:
                        raise AttributeError(self.creator.label,  route, route.__class__, route.next_hop, route.next_hop.__class__)

        # elif scope == utils6.IPV6_ADDR_MULTICAST:
        #     #self.iface.send(p,  self.get_macst_mac(p.dst))
        #     return dst_ip

    def route_add(self, route):
        added = False
        for i, dst in enumerate(self):
            if dst == route:
                self[i] = route
                added = True
                # raise
        if not added:
            self.append(route)
        self.sort()
        
        self.creator.add_to_history('Added route ', str(route) + '  (' + route.__class__.__name__ + ')')
    
    def route_del(self, route):
        for i, dst in enumerate(self):
            if dst == route:
                del(self[i])
                return
                
    def index(self, addr):
        for i, dst in enumerate(self):
            if dst == addr: return i
                
    def __str__(self):
        s = ''
        for i, dst in enumerate(self):
            s += str(i) + ' : ' + str(dst) + str(dst.next_hop) + str(dst.author) +  '\n'
        return s


class MobileIPv6(object):
    def __init__(self, node, HA_addr, home_prefix, prefix_len = 64, label='' ):
        self.node = node
        self.home_prefix = home_prefix
        self.prefix_len = prefix_len
        self.HA_addr = IPv6Addr(HA_addr)
        # self.home_iface = interfaces.MobileIPv6Tunnel(self.node, addr = self.HA_addr, tun_peer_addr = self.HA_addr)
        self.is_homeagent = issubclass(node.__class__, nodes.HomeAgent)
        self.tunnels = {}
        if self.is_homeagent:
            self.binding_cache = {}
            dst = IPv6Prefix(home_prefix, 
                            prefixlen = prefix_len,
                            author = self, 
                            OnLinkFlag = True,
                            next_hop = self.node.loopback)
            self.node.rt6.route_add(dst)
        else:
            self.binding_update_list = {}
        
    def handle_ipv6_binding_update_real(self, p, iface = None):
        p.add_to_trip(self.node, 'retired')
        coa = IPv6Addr(p[inet6.IPv6].src)
        hoa = p[inet6.HAO].hoa
        try:
            tun = self.binding_cache[hoa]
            tun.tun_peer_addr = coa
        except KeyError:
            label = 'tun_' + str(coa)
            tun = self.binding_cache[hoa] = interfaces.MobileIPv6Tunnel(
                                        self.node,
                                        top_addr = None,
                                        tun_addr = self.HA_addr,
                                        tun_peer_addr = coa,
                                        label = label)
            route = IPv6Prefix(hoa, 
                            prefixlen = 128,
                            iface = None,
                            author = self, 
                            OnLinkFlag = False,
                            next_hop = tun)
            self.node.rt6.route_add(route)
        self.node.add_to_history('binding cache modified', str(self.binding_cache))
        self.send_binding_acknowledgement(coa)

    # def handle_ipv6_binding_update_real(self, p, iface = None):
    #     p.add_to_trip(self.node, 'retired')
    #     hoa = p[inet6.HAO].hoa
    #     coa = IPv6Addr(p[inet6.IPv6].src)
    # 
    #     try:
    #         tun = self.binding_cache[hoa]
    #         tun.tun_peer_addr = coa
    #     except KeyError:
    #         label = 'tun_' + str(coa)
    #         tun = self.binding_cache[hoa] = interfaces.MobileIPv6Tunnel(
    #                                     self.node,
    #                                     top_addr = None,
    #                                     tun_addr = self.HA_addr,
    #                                     tun_peer_addr = coa,
    #                                     label = label)
    #         route = IPv6Prefix(hoa, 
    #                         prefixlen = 128,
    #                         iface = None,
    #                         author = self, 
    #                         OnLinkFlag = False,
    #                         next_hop = tun)
    #         self.node.rt6.route_add(route)
    #     self.node.add_to_history('binding cache modified', str(self.binding_cache))
    #     self.send_binding_acknowledgement(coa)
    #     

    def handle_ipv6_binding_update(self, p, iface = None):
        p.add_to_trip(self.node, 'retired')
        hoa = p[inet6.HAO].hoa
        coa = IPv6Addr(p[inet6.IPv6].src)
        # FIXME
        if hoa not in self.binding_cache:
            self.binding_cache[hoa] = {}
        for iface, coa in p.misc['bindings'].iteritems():
            if iface in self.binding_cache[hoa]:
                tun = self.binding_cache[hoa][iface]
                tun.tun_peer_addr = coa
            else:
                label = 'tun_' + str(coa) + iface.label
                tun = self.binding_cache[hoa][iface] = interfaces.MobileIPv6Tunnel(
                                        self.node,
                                        top_addr = None,
                                        tun_addr = self.HA_addr,
                                        tun_peer_addr = coa,
                                        label = label)
                route = IPv6Prefix(hoa, 
                            prefixlen = 128,
                            iface = None,
                            author = self, 
                            OnLinkFlag = False,
                            next_hop = tun)
                self.node.rt6.route_add(route)

                    
        self.node.add_to_history('binding cache modified', str(self.binding_cache))
        self.send_binding_acknowledgement(coa)


    def send_binding_update(self, iface):
    
        #RFC3775 MIPv6 (6.1.7 & 11.7.1) Binding Update Message sending

        # Compute the binding update message and send it
        # Source Address = care-of address
        #TODO: handle sequence number in MIP6MH_BU
        
        CoA = self.node.which_ipv6_src_address_old(str(self.HA_addr), iface)

        p = inet6.IPv6(dst=str(self.HA_addr), src=str(CoA)) / \
            inet6.IPv6ExtHdrDestOpt(options=inet6.HAO(hoa=str(self.node.HoA))) / \
            inet6.MIP6MH_BU(options=inet6.MIP6OptAltCoA(acoa=str(CoA)))
        
        #self.HA_seq += 1
        p = Packet(iface, p, 'Binding Update', 'MIPv6')
        
        #FIXME
        f = filter(lambda iface: iface.__class__ == interfaces.MobileIPv6Tunnel and iface.active ==True, self.node.interfaces)
        bindings = {}
        for iface in f:
            bindings[iface] = CoA
        p.misc['bindings'] = bindings
        #END FIXME
            
        
        self.node.route_ipv6_old(p, iface)
        

    def handle_ipv6_ipv6(self, p, iface):
        p.remove_from_bottom(1)
        p.add_to_trip(self.node, 'detunneled')
        if self.is_homeagent:
            hoa = p.src
            try:
                tun = self.binding_cache[hoa]
            except:
                raise KeyError(str(hoa) + ' not in '+ str(self.binding_cache))
        else:
            tun = self.binding_update_list[iface]
        if tun.__class__ == interfaces.MobileIPv6Tunnel:
            tun.receive(p)
        else:
            for iface, tunnel in tun.iteritems():
                tunnel.receive(p)
                return

    def send_binding_acknowledgement(self, CoA):
        #src = self.which_ipv6_src_address(str(CoA))
        p = inet6.IPv6(dst= str(CoA), src=str(self.HA_addr)) / \
            inet6.IPv6ExtHdrRouting(type=2, addresses=['::1']) / \
            inet6.MIP6MH_BA()

        p = Packet(self.node, p, 'Binding Acknowledgement', 'MIPv6')
        self.node.route_ipv6(p) #TODO: R Check correctness in Draft MCoA

    def handle_ipv6_binding_acknowledgement(self, p, iface):
        p.add_to_trip(self.node, 'retired')
        pass
    
    def global_ipv6_notification(self, iface, addr):
        coa = addr
        # tun = self.create_or_activate_tunnel(self.node.HoA, coa, self.HA_addr, iface)
        assert iface
        try:
            tun = self.binding_update_list[iface]
            tun.tun_addr = coa
            tun.active = True
        except KeyError:
            label = 'tun_' + iface.label
            tun = self.binding_update_list[iface] = interfaces.MobileIPv6Tunnel(
                                                self.node, 
                                                top_addr = self.node.HoA, 
                                                tun_addr = coa,
                                                tun_peer_addr = self.HA_addr, 
                                                label=label, 
                                                iface=iface)
        self.node.add_to_history('binding update list modified', str(self.binding_update_list))            
        self.send_binding_update(iface)



    def disconnect_notification(self, iface):
        try:
            tun = self.binding_update_list[iface]
        except KeyError:
            return
        tun.active = False
        
                    # 
                    # tun.active = False
                    # if tun == self.current_tunnel:
                    #     for iface in self.interfaces:
                    #         if iface.__class__ == interfaces.MobileIPv6Tunnel and iface.active:
                    #             self.current_tunnel = iface
                    #             self.send_binding_update(iface.iface)
                    #         else:
                    #             self.current_tunnel = None
        
    # def deactivate_tunnel(self, iface):
    #      if iface in self.tunnels:
    #          tun = self.tunnels[iface]
    #          tun.active = False
    #          return tun
 

class IPv6Addr(IPv6Prefix):
    def __init__(self, addr, iface=None, author = None):
        IPv6Prefix.__init__(self, addr, 128, iface, None, author)

    def get_sol_node_mcast(self):
        return IPv6Addr(utils6.in6_getnsma(self.addr), self.iface)

    def __eq__(self, other):
        if type(other) == str:
            other = IPv6Addr(other)
        if other.iface and self.iface and other.iface <> self.iface:
            return False
        return other.prefixlen == self.prefixlen and other.addr == self.addr 
    # def get_ip_mcast(self):
    #     return utils6.in6_getLinkScopedMcastAddr(self.addr)
    
    def get_mac_mcast(self):
        if self.is_multicast:
            return utils6.in6_getnsmac(self.addr)
        else:
            return self.get_sol_node_mcast().get_mac_mcast()
            # print 'Input must be a multicast IPv6 Address' + str( self.is_multicast) 
        

class NeighborCacheEntry(IPv6Addr):
    'RFC 2461 page 33'
    def __init__(self, addr, iface, state, author = None, mac=None, is_router = False):
        if not iface:
            raise AttributeError('A neighbor cache entry must have an interface')
        IPv6Addr.__init__(self, addr, iface, author)
        self.state = state
        self.mac = mac
        self.is_router = is_router
        self.retransmit_counter = retransmit_counter = 30
        self.queue = []
        self.will_be_unreachable_at = None
        self.unanswered_probes = 0
    
    @property
    def scope(self):
        return utils6.IPV6_ADDR_LINKLOCAL
    
    # def __str__(self):
    #     return '%s, isrouter = %s, state = %s' % (IPv6Addr.__str__(self), 
    #                                             self.is_router, self.state)

class MobileIPv6CacheEntry(IPv6Addr):
    pass
    
class IPv6Addresses(AddressList):

    def register(self, addr):
        self.append(addr)
        
    def append(self, addr):
        if addr.__class__ <> IPv6Addr:
            addr = IPv6Addr(addr)
            
        if addr not in self:# and addr.author:
            list.append(self, addr)
            self.creator.add_to_history('Added IPv6 address', addr)
        else:
            print 'WARNING: Duplicate IPv6 Address', addr, addr.author, self
            raise AttributeError(str(addr) + ' already in '+ str(self))
        
    def globals(self):
        return filter(lambda a: a.is_global, self)
        
    def link_locals(self):
        return filter(lambda x: x.is_linklocal, self)


    def flush(self, author = None):
        AddressList.flush(self, author)
        self.creator.add_to_history('IPv6 removed all addresses')
def mac2linklocal(mac):
    return 'FE80::'+ utils6.in6_mactoifaceid(mac)
    
class ICMPv64Host(object):

    def __init__(self, ipv6,
                    DupAddrDetectTransmits=1,
                    RSTransmits=3,
                    NSTransmits=3,
                    RetransTimer=1):
        #NetpylabThread.__init__(self, iface)
        
        #self.addresses = []
        self.ipv6 = ipv6
        self.world = ipv6.world
        self.node = self.ipv6.node
        self.iface = ipv6.iface
        self.rt6 = self.node.rt6
        
        self.is_router = self.node.forwarding
        
        self.DupAddrDetectTransmits = DupAddrDetectTransmits
        self.RSTransmits=RSTransmits
        self.NSTransmits=NSTransmits
        
        self.ManagedFlag = False
        self.OtherConfigFlag = False
        
        # Default values that can be overridden by router advertisements
        #RFC 2461 page 50
        self.LinkMTU = 1500 
        self.CurHopLimit = 255 #TODO Conform to RFC
        self.ReachableTime = 30 # Not RFC Compliant, must be randomized
        self.RetransTimer = RetransTimer
        
        self.INCOMPLETE, self.REACHABLE, self.STALE, self.DELAY, self.PROBE = range(5)

        self.reset()
        
    def start(self):
        # join all nodes multicast
        
        self.all_nodes_mcast = IPv6Addr('FF02::1', self.iface, author = self)
        self.all_routers_mcast = IPv6Addr('FF02::2', self.iface, author = self)
        self.register_mcast(self.all_nodes_mcast)
        if self.is_router:
            self.register_mcast(self.all_routers_mcast)
        
        self.configure_addr(mac2linklocal(self.iface.mac))
        for addr in self.ipv6.manual_addresses:
            self.configure_addr(addr)
        if not self.is_router:
            # Send a Router Sollicitations
            self.router_solicitation_procedure(self.RSTransmits)
        #NetpylabThread.start(self)

    def reset(self):
        self.rt6.flush(self)
        self.ipv6.addresses.flush(self)
        self.ipv6.mac_mcast_addresses = []
        self.known_prefixes = []
        self.received_ra = False
        self.has_global = False
        self.tentatives = []
        
        

    def register_mcast(self, ip_addr):
        self.ipv6.addresses.register(ip_addr)
        self.ipv6.register_mac_mcast(ip_addr.get_mac_mcast())
    
    def unregister_mcast(self, ip_addr):
        self.ipv6.addresses.remove(ip_addr)
        self.ipv6.unregister_mac_mcast(ip_addr.get_mac_mcast())
        
    def configure_addr(self, addr):
        a = IPv6Addr(addr, iface =self.iface, author = self)
        m = a.get_sol_node_mcast()
        m.author = self
        self.register_mcast(m)
        self.tentatives.append(a)
        self.send_neighbor_solicitation_dad((a,m))
        #self.iface.world.event(self.RetransTimer, self.timeout_ns_dad, a)
        CallLater(self, self.RetransTimer, self.timeout_ns_dad, a)
        
    def router_solicitation_procedure(self, remaining_sol):
        if self.received_ra:
            return
        src_ip = self.ipv6.linklocal_addr if self.ipv6.linklocal_addr else IPv6Addr('::')
        self.send_router_solicitation(src_ip)
        if remaining_sol > 1:
            # Wait for a response
            CallLater(self, self.RetransTimer, self.router_solicitation_procedure, remaining_sol - 1)
            
            # self.iface.world.event(self.RetransTimer, 
            #                         self.router_solicitation_procedure, 
            #                         remaining_sol - 1)
                                    
    def receive_router_solicitation(self, p):
        p.add_to_trip(self.iface, 'retired')
        pass


    # def timeout_rs(self):
    #     # Check if we received an RA
    #     # Otherwise ....
    #     #self.remaining_RSTransmits -= 1
    #     if self.remaining_RSTransmits > 0:
    #         self.send_router_solicitation()
    #         self.iface.world.event(self.RetransTimer, self.timeout_rs)
            
                

    # def sendND_NSDAD(self, tentative_addr, send_rs = False):
    def send_neighbor_solicitation_dad(self, addr_mcast):
        """
            Send the Neighbor Solicitation message to see if the solicited
            address is already used.
            To check an address, a node sends DupAddrDetectTransmits Neighbor
            Solicitations, each separated by RetransTimer milliseconds. The
            solicitation’s Target Address is set to the address being checked,
            the IP source is set to the unspecified address and the IP
            destination is set to the solicited-node multicast address of the
            target address.
        """
        
        # p = (l2.Ether(dst=self.mac_multicast, src=self.iface.mac)/
        #         inet6.IPv6(dst=self.solicited_node_mcast, src='::', hlim=255)/
        #         inet6.ICMPv6ND_NS(tgt=self.tentative_addr))
        
        addr, mcast = addr_mcast
        
        self.send_neighbor_solicitation(mcast.get_mac_mcast(), src_ip='::', dst_ip=str(mcast), target=str(addr))
        
        # p = Packet(self.iface,
        #     inet6.IPv6(dst=str(mcast), src='::', hlim=255)/
        #     inet6.ICMPv6ND_NS(tgt=str(addr)))
        # self.iface.send(p, mcast.get_mac_mcast())
    
    def timeout_ns_dad(self, addr):
        # Check that we did not receive a Neighbor Advertisement
        if not addr in self.tentatives:
            assert False
        #TODO : check if this is the good way to do that
        self.ipv6.addresses.register(addr)
        if not self.ipv6.linklocal_addr and addr.is_linklocal:
            self.ipv6.linklocal_addr = addr
            self.world.log.info('%s.ipv6.icmpv6 got a link local address %s'%(self.iface, addr))
            for prefix in self.known_prefixes:
                self.configure_global_ipv6_from_prefix(prefix, self.iface.mac)
        elif addr.is_global and not self.has_global:
            self.has_global = True
            self.world.log.info('%s.ipv6.icmpv6 got a global address %s'%(self.iface, addr))
            self.node.global_ipv6_notification(self.iface, addr)
        self.tentatives.remove(addr)
            
    
    def configure_global_ipv6_from_prefix(self, prefix, mac):
        globaddress = prefix.mac2ip(mac) #FIXME not mac but lladdr
        globaddress.author = self
        self.ipv6.addresses.register(globaddress)
        if not self.has_global:
            self.has_global = True
            self.node.global_ipv6_notification(self.iface, globaddress)
        
    def send_router_solicitation(self, source_ip):
        """
            Send a Router Solicitation to get information about the routers on the link
            and informations about the link itself (prefix, prefix length).
            RFC 2461 page 17
        """
        
        rtsol = inet6.IPv6(dst=str(self.all_routers_mcast),src= str(source_ip),hlim=255) 
        rtsol /= inet6.ICMPv6ND_RS()
        
        if not source_ip == "::":
            rtsol /= inet6.ICMPv6NDOptSrcLLAddr(lladdr = self.iface.mac)
        
        p = Packet(self.iface, rtsol, 'Router Sollicitation', 'ICMPv6')
        self.iface.send(p, self.all_routers_mcast.get_mac_mcast())
    
    def send_echo_request(self, macdstaddr, ipdstaddr):
        """
            Send an echo request.
        """
        req = l2.Ether(dst=macdstaddr, src=self.iface.mac)
        # check if destination is LL or Global
        req /= inet6.IPv6(dst= ipdstaddr, src=self.ipv6.addresses[0])/inet6.ICMPv6EchoRequest()#TODO : verify that the src IP @ is the link local @ of the interface
        self.iface.send(req)
        
    def receive_neighbor_solicitation(self, p):
        #TODO: Validation RFC 2461
        p.add_to_trip(self.iface, 'retired')
        target = IPv6Addr(p[inet6.ICMPv6ND_NS].tgt)
        if target in self.tentatives:
            if p[inet6.IPv6].src == '::': # unspecified
                #TODO: Check if I did not send the packet to myself (multicast loopback)
                self.tentatives.remove(target)
                self.world.log.warning("Duplicate Address Discovered for " +self.iface.label)
            else: # address is unicast
            #the solicitation’s sender is performing address resolution on
            #the target; the solicitation should be silently ignored.
                return
        else:
            # the solicitation is processed as described in [DISCOVERY]
            if p[inet6.IPv6].src == '::':
                sollicited = False
                dst_ip  = self.all_nodes_mcast
                dst_mac = self.all_nodes_mcast.get_mac_mcast()
            else:
                nce = self.check_if_mac_changed(p, is_router = False)
                sollicited = True
                dst_ip  = p[inet6.IPv6].src
                dst_mac = nce.mac
            self.send_neighbor_advertisement(dst_mac = dst_mac, dst_ip=dst_ip, target= str(target), solicited = True, override =True)
        

        
        # if packet[inet6.IPv6].dst in self.registeredmulticastaddr:
        #     if packet[inet6.IPv6].src == '::': #A node solicitates an @
        #         if packet[ICMPv6ND_NS].tgt in self.solicitedaddress: # check that its one of the sollicited IPv6 addresses
        #             dstmacaddr = '33:33:00:00:00:01'
        #             resp = Ether(src=self.iface.mac,dst=dstmacaddr)
        #             resp /= IPv6(dst='FF02::1',src=self.iface.addresses[0],hlim=255)#TODO : verify that the src IP @ is the link local @ of the interface
        #             resp /= ICMPv6ND_NA.answers(packet[ICMPv6ND_NS]) #Warning !!! Verify the use of the function
        #             resp /= ICMPv6NDOptDstLLAddr(lladdr=self.iface.mac)
        #             self.iface.send(resp, packet[ICMPv6NDOptSrcLLAddr].lladdr)
        #     else: #Request for address resolution
        #         self.table[packet[inet6.IPv6].src]=packet[ICMPv6NDOptSrcLLAddr].lladdr
        #         pktsrc = packet[inet6.IPv6].src
        #         target = packet[ICMPv6ND_NS].tgt
        #         resp = Ether(dst=packet[ICMPv6NDOptSrcLLAddr].lladdr,src=self.iface.mac)/IPv6(dst=pktsrc,src=target,hlim=255)
        #         resp /= ICMPv6ND_NA.answers(packet[ICMPv6ND_NS]) #Warning !!! Verify the use of the function
        #         resp /= ICMPv6NDOptDstLLAddr(lladdr=self.iface.mac)
        #         self.iface.send(resp, packet[ICMPv6NDOptSrcLLAddr].lladdr)
    
    def receive_neighbor_advertisement(self, p):
        p.add_to_trip(self.iface, 'retired')
        p = p[inet6.ICMPv6ND_NA]
        target = IPv6Addr(p.tgt, self.iface)
        
        is_router = p.R
        solicited = p.S
        override = p.O
        
        if target in self.tentatives:
                self.tentatives.remove(target)
                self.world.log.warning("Duplicate Address Discovered for " +self.iface.label)
                return
        
        i = self.rt6.index(target)
        if i == None:
            assert None
            return
    
        
        nce = self.rt6[i]
        new_mac = p.lladdr
        same_mac = (nce.mac == new_mac)
        has_option = True

        if nce.state == self.INCOMPLETE:
            if has_option:
                nce.mac = new_mac
                for waiting_p in nce.queue:
                    waiting_p.add_to_trip(self.iface, 'dequeued')
                    self.iface.send(waiting_p, nce.mac)
                nce.queue = []
                
                nce.is_router = is_router #(**)
                if solicited: nce.state = self.REACHABLE
                else: nce.state = self.STALE
                    
        elif nce.state in (self.REACHABLE, self.STALE, self.DELAY, self.PROBE):
            if has_option:
                if override:
                    if same_mac:
                        nce.mac = new_mac
                        if not solicited: nce.state = self.STALE
                    if solicited: nce.state = self.REACHABLE
                    nce.is_router = is_router #(**)
                else: # not override
                    if not same_mac:
                        if nce.state == self.INCOMPLETE:
                            nce.state = self.STALE
                        else: # other states
                            nce.is_router = is_router #(**)
                            if solicited: nce.state = self.REACHABLE
            else: # no lladdr option
                nce.is_router = is_router #(**)
                if solicited: nce.state = self.REACHABLE
                                

    def check_if_mac_changed(self, p, is_router):
        """Checks if mac address changed compared to the one in the context, 
        create it if necessary and sets it to STALE state if mac changes"""
        src = IPv6Addr(p[inet6.IPv6].src, iface = self.iface)
        mac = p.lladdr
        i = self.rt6.index(src)
        if i != None: 
            nce = self.rt6[i]
            if mac != nce.mac:
                nce.state = self.STALE
            nce.mac = mac
            if nce.state == self.INCOMPLETE:
                for waiting_p in nce.queue:
                    waiting_p.add_to_trip(self.iface, 'dequeued')
                    self.iface.send(waiting_p, nce.mac)
                nce.queue = []
        else:
            nce = NeighborCacheEntry(addr = p[inet6.IPv6].src, 
                        iface = self.iface,
                        state = self.STALE, 
                        author = self, 
                        mac=mac, 
                        is_router = is_router)
            self.rt6.route_add(nce)
        return nce
    
    def upper_layer_advice(self, address):
        if address in self.destination_cache:
            #TODO: find the corresponding neighbor
            if neighbor in self.neighbor_cache:
                self.neighbor_cache[neighbor].state = self.REACHABLE
    
    def receive_router_advertisement(self, p, is_router = False):
        p.add_to_trip(self.iface, 'retired')
        #TODO: Check Validity
        nce = self.check_if_mac_changed(p, is_router = True)
        if is_router:
            return 

        if not self.received_ra:
            self.received_ra = True
            self.world.log.info('%s.ipv6.icmpv6 received his first Router Advertisment' %self.iface)
        
        #src = p[inet6.IPv6].src

        # if not src in self.default_routers:
        #     self.default_routers.append(src)
        # nce = NeighborCacheEntry(addr = p[inet6.IPv6].src, 
        #                     iface = self.iface,
        #                     state = self.STALE, 
        #                     author = self, 
        #                     mac=p.lladdr, 
        #                     is_router = True)
                            
        prefix = IPv6Prefix('::', 
                            prefixlen = 0,
                            iface = self.iface,
                            author = self, 
                            OnLinkFlag = False,
                            next_hop = nce)
        if prefix not in self.node.rt6:
            self.rt6.route_add(prefix)

        is_managed = p.M
        if not self.ManagedFlag and is_managed:
            #TODO : implement stateful configuration if needed
            pass
        self.ManagedFlag = is_managed
        if is_managed: return # for the moment
        
        if p.chlim:
            self.CurHopLimit = p.chlim
        
        if p.retranstimer:
            self.RetransTimer = p.retranstimer

        if p.reachabletime:
            self.ReachableTime = p.reachable_time
        
        if inet6.ICMPv6NDOptMTU in p.data:
            if p.mtu : self.LinkMTU = p.mtu

        for i in xrange(1,100):
            try:
                prefix_opt = p[inet6.ICMPv6NDOptPrefixInfo:i]
            except:
                break
            
            if not prefix_opt: break
            if not prefix_opt.A: continue
            if prefix_opt.prefix == 'FE80::': continue
            if prefix_opt.preferredlifetime > prefix_opt.validlifetime:
                self.iface.world.log.warning('RA preferred lifetime is greater than the valid lifetime')
                continue
            
            prefix = IPv6Prefix(prefix_opt.prefix, prefix_opt.prefixlen, OnLinkFlag = True, author = self, next_hop = self.iface)
            if prefix not in self.rt6:
                self.rt6.route_add(prefix)
            if prefix not in self.known_prefixes:
                self.known_prefixes.append(prefix)
                if self.ipv6.linklocal_addr:
                    self.configure_global_ipv6_from_prefix(prefix, self.iface.mac)



    def create_neighbor(self, addr):
        nce = NeighborCacheEntry(addr = addr, iface = self.iface,
                    state = self.INCOMPLETE, author = self, mac=None, is_router = True)
        self.node.rt6.route_add(nce)
        self.retransmit_ns(nce)
        return nce

    def send(self, p, nce):
        "RFC 2461 page 34"
        if not self.ipv6.linklocal_addr:
            self.world.log.warning(self.iface.label +'.ipv6.icmpv6 cannot send packet: no link local address')
            return
        if nce.state == self.INCOMPLETE:
            nce.queue.append(p)
            if len(nce.queue) > 3:
                nce.queue[0].add_to_trip(self.iface, 'deleted')
                del(nce.queue[0])
            p.add_to_trip(self.iface, 'enqueued', info = 'already sent an NS to ' + str(nce))
            return
        
        elif nce.state == self.REACHABLE:
            if self.iface.world.time > nce.will_be_unreachable_at:
                nce.status = self.DELAY
                self.start_delay_timer()
        elif nce.state == self.STALE:
            nce.status = self.DELAY
            self.start_delay_timer()

        # in all cases where packet is not enqueued, send it
        if nce.mac == None:
            raise 'Problem'
        self.iface.send(p, nce.mac)
            
    
    def start_delay_timer(self):
        pass

    def retransmit_ns(self, nce):
        # nce = self.neighbor_cache[next_hop_ip]
        if not self.ipv6.linklocal_addr:
            self.world.log.error('Want to retransmit neighbor solicitation but no link local address')
            return
        #print self.iface, nce, nce.state
        if nce.state <> self.INCOMPLETE:
            self.world.log.info(self.iface.label + '.ipv6.icmpv6 retransmit_ns error: Neigbor Cache State is not INCOMPLETE')
            return
        nce.retransmit_counter -=1
        if nce.retransmit_counter < 0:
        #Discard Cache Entry
            self.rt6.route_del(nce)
            #TODO: Send ICMP Error
            return
        # sends a multicast Neighbor Solicitation
        self.send_neighbor_solicitation(nce.get_mac_mcast(), self.ipv6.linklocal_addr, nce, nce)
        # start retransmit timer
        CallLater(self, self.RetransTimer, self.retransmit_ns, nce)
        # self.iface.world.event(self.RetransTimer, self.retransmit_ns, nce)
        
        
    def send_neighbor_solicitation(self, dst_mac, src_ip, dst_ip, target):
        """
            RFC 2461 page 21
        """
        nsol = inet6.IPv6(dst= str(dst_ip).split('%')[0], src=str(src_ip), hlim=255)/ \
            inet6.ICMPv6ND_NS(tgt=str(target).split('%')[0])
            
        if not src_ip == IPv6Addr('::'):
             nsol /= inet6.ICMPv6NDOptSrcLLAddr(lladdr=self.iface.mac)
             
        p = Packet(self.iface, nsol, "Neighbor Solicitation", 'ICMPv6')
        self.iface.send(p, dst_mac)

    def send_neighbor_advertisement(self, dst_mac, dst_ip, target, solicited, override):
        """
            RFC 2461 page 23
        """
        if not self.ipv6.linklocal_addr:
            return
        nadv = inet6.IPv6(dst=str(dst_ip), src=str(self.ipv6.linklocal_addr), hlim=255)/ \
            inet6.ICMPv6ND_NA(R=self.is_router, S= solicited, 
                                            O = override, tgt = str(target))/ \
            inet6.ICMPv6NDOptSrcLLAddr(lladdr=self.iface.mac)
        p=Packet(self.iface, nadv, 'Neighbor Advertisement', 'ICMPv6')
        self.iface.send(p, dst_mac)


    def send_redirect_message(self):
        #TODO: implement ?
        pass 
    
    # def get_macst_mac(self, ipv6_addr):
    #     ip_binary = socket.inet_pton(socket.AF_INET6, ipv6_addr)
    #     return utils6.in6_getnsmac(t_binary)

##########################################################################################################  
##########################################################################################################  
##########################################################################################################  
##########################################################################################################
#modified by b.gaultier 26/05  
# 
# class ICMPv64MNN(ICMPv64Host):
#     
#     
#     def __init__(self, iface, HoA, HA_addr):
#       self.HoA = HoA
#       self.HA_addr = HA_addr
#         self.CoA = None
#       #self.HA_seq = 0 #TODO R See seq number initialization
#       self.is_associated = False
#         # TODO: Improve is_associated (only one HA is possible in this version) with a real BUL (RFC 3775 11.1. The Binding Update)
#       ICMPv64Host.__init__(self, iface)
#             
#             
#     def receive_router_advertisement(self, packet, is_router = False):
#         #If we received a RA, we have to build our CoA and Send a BU
#         #globaddress
#         #TODO: if the prefix is in the home network, do nothing!
#         ICMPv64Host.receive_router_advertisement(self, packet)
#         #R Check if we have global before sending
#         self.CoA = globaddress
#         if not self.CoA:
#             # We MUST have an CoA configured to send a BU!
#             raise
#         else:
#             self.send_binding_update(self,CoA)

    #R define timeout_ns ....
    
    
    
#    def configure_globaddress(self):
#        # Test if global address is already configured
#        if len(self.iface.addresses) >= 1:
#            # TODO: Improve this part
#            # Ok, we have an global adress so we can use it
#            self.CoA = self.iface.addresses[1]
#        else :
#            # wait for RA
#            timeout_ns(self)
            
        
    # 
    #     
    #     def send_binding_update(self, CoA):
    #     
    #         #RFC3775 MIPv6 (6.1.7 & 11.7.1) Binding Update Message sending
    # 
    #         # Compute the binding update message and send it
    #         # Source Address = care-of address
    #         #TODO: handle sequence number in MIP6MH_BU
    # 
    #         p =   inet6.IPv6(dst=HA_addr,src=str(self.ipv6.linklocal_addr)) / \
    #           inet6.MIP6MH_BU() / \
    #             int.HAO()
    #             #inet6.IPv6ExtHdrDestOpt(options=[inet6.HAO(hoa=self.HoA)])
    #         self.HA_seq += 1
    #         p = Packet(self.iface, p, 'Binding Update', 'MIPv6')
    #         self.iface.send(p) #TODO: R Check correctness in Draft MCoA
    #         
    #     def receive_mobile_ipv6_packet(self, packet):
    #         t = p.TypeFlag 
    #         if t == BA:
    #             self.receive_binding_acknowledgement()
    #         elif t == ERROR:
    #             self.receive_binding_error()
    #         
    #     def receive_binding_acknowledgement(packet):
    #         #TODO: R Check packet correctness
    #         # First verify the HA_addr
    #         src = packet[inet6.IPv6].src
    #         if src == self.HA_addr:
    #             self.is_associated =True
    #         else:
    #             # The HA_addr did not correpond with the node which answer to our BU 
    #             raise        
    #        
    #        
    # class ICMPv64HA(ICMPv64Host):
    # 
    #     def __init__(self, association_table):
    #         self.binding_update_list = {}
    #     
    #     def receive_mobile_ipv6_packet(self, packet):
    #         t = p.TypeFlag 
    #         if t == BU:
    #             self.receive_binding_update()
    #         elif t == ERROR:
    #             self.receive_binding_error()
#        else:
#            raise: 
        
    # def receive_binding_update(packet):
    #     # Build Association table
    #     CoA_MNN = IPv6Addr(packet[inet6.IPv6].src)
    #     HoA_MNN = IPv6Addr(packet[inet6.HAO].hoa)
    #     if HoA_MNN in self.binding_update_list:
    #         print '4WAAAAAAAAAAAAAAAAAAAAAAAYYYYYYY'
    #     self.binding_update_list[HoA_MNN] = CoA_MNN
    # 
    #         self.
    #         #TODO: R refresh
    #    # else:
    #    #     # Add a new association
    #    #     self.binding_update_list[HoA_MNN] = CoA_MNN

##########################################################################################################  
##########################################################################################################  
##########################################################################################################  
##########################################################################################################  
  
class ICMPv64Router(ICMPv64Host):

    # Router Configuration RFC 2461 page 40
    def __init__(self, iface,
                AdvSendAdvertisements =True,
                MaxRtrAdvInterval = 600,
                MinRtrAdvInterval = 200,
                AdvManagedFlag = False,
                AdvOtherConfigFlag = False,
                AdvLinkMTU = 1500, #TODO Modify according to RFC
                AdvReachableTime = 0,
                AdvRetransTimer = 0,
                AdvCurHopLimit = 255, #TODO Modify according to RFC
                AdvDefaultLifetime = 1800,
                AdvPrefixList = []
                ):
        #self.is_router = True
        ICMPv64Host.__init__(self, iface)
        # Router Configuration RFC 2461 page 40
        self.AdvSendAdvertisements = AdvSendAdvertisements
        self.MaxRtrAdvInterval = MaxRtrAdvInterval
        self.MinRtrAdvInterval = MinRtrAdvInterval
        self.ManagedFlag = AdvManagedFlag
        self.OtherConfigFlag = AdvOtherConfigFlag
        self.LinkMTU =  AdvLinkMTU
        self.ReachableTime = AdvReachableTime
        self.RetransTimer = AdvRetransTimer if AdvRetransTimer else 1
        self.CurHopLimit = AdvCurHopLimit
        self.DefaultLifetime = AdvDefaultLifetime
        self.set_prefix_list(AdvPrefixList)

    
    def set_prefix_list(self, AdvPrefixList):
        self.AdvPrefixList = AdvPrefixList
        for p, plen in AdvPrefixList:
            prefix = IPv6Prefix(p, plen, OnLinkFlag = True, author = self, next_hop = self.iface)
            self.rt6.route_add(prefix)
                    
    def start(self):
        ICMPv64Host.start(self)
        self.periodic_send_ra()

    def periodic_send_ra(self):
        if self.AdvSendAdvertisements:
            #if hasattr(self, 'ra_timer'):
            try: self.ra_timer.cancel()
            except: pass
            delay = (self.MaxRtrAdvInterval + self.MinRtrAdvInterval)/2
            #TODO comply with RFC 2461 Page 46 for the delay
            delay = 2 # Not RFC compliant
            self.ra_timer = CallLater(self, delay, self.send_router_advertisement)
            #self.iface.world.event( delay, )
            

    def send_router_advertisement(self):
        """ RFC 2461 page 18 """
        if self.ipv6.linklocal_addr:
            rtadv = inet6.IPv6(dst= str(self.all_nodes_mcast),src= str(self.ipv6.linklocal_addr) ,hlim=255) / \
                inet6.ICMPv6ND_RA(
                        chlim= self.CurHopLimit, 
                        M=self.ManagedFlag, 
                        O=self.OtherConfigFlag, 
                        reachabletime =self.ReachableTime, 
                        retranstimer = self.RetransTimer)/ \
                inet6.ICMPv6NDOptSrcLLAddr(lladdr = self.iface.mac)/ \
                inet6.ICMPv6NDOptMTU(mtu=self.LinkMTU)

            for (prefix, prefixlen) in self.AdvPrefixList:
                rtadv /= inet6.ICMPv6NDOptPrefixInfo(prefix=prefix, prefixlen = prefixlen )
            
            p = Packet(self.iface, rtadv, 'Router Advertisement', 'ICMPv6')
            self.iface.send(p, self.all_nodes_mcast.get_mac_mcast())
            self.periodic_send_ra()
            
    
    def receive_router_solicitation(self, p):
        if p[inet6.IPv6].src != '::':
            self.check_if_mac_changed(p, is_router = False) # check if the neighbor cache is up-to-date
        #delay = 1 # TODO: comply with RFC 62461 page 47
        #self.ra_timer = self.iface.world.event( delay, self.send_router_advertisement)
        self.send_router_advertisement()

    def receive_router_advertisement(self, p):
        ICMPv64Host.receive_router_advertisement(self, p, is_router = True)
        #TODO: RFC 2461 page 48
        pass

# 
# class MobileIPv64Host(object):
#     def __init__(self, HoA, HA_addr):
#         self.HoA = IPv6Addr(HoA)
#         self.HA_addr = IPv6Addr(HA_addr)
#         self.bul = []
# 
#     def start(self):
#         pass
#         
#     def send_binding_update(self, CoA):
#         # Add the entry in the binding update list
#         self.bul[0]={'HAAddr' : self.HAAddr, 'HoA' :self.HoA, 'CoA' : CoA, 'maxSequenceNumber': 0, 'State':False}
#         # Compute the binding update message and send it
#         bu = inet6.IPv6(dst= self.HAAddr, src= CoA) / \
#                 inet6.MIP6MH_BU(seq=(self.bindingUpdateList[0]['maxSequenceNumber']+1) % 65536)  /\
#                 inet6.IPv6ExtHdrDestOpt(options=[inet6.HAO(hoa=self.HoA)])
#         p = Packet(self.iface, bu, 'Binding Update', 'MIPv6')
#         self.iface.send(p, self.iface.mac)
#     
#     def receive(self, p):
#         pass
# 
# class MobileIPv64HA(object):
#     
#     def receive_binding_update(self, p):
#         dst = None
#         src = None
#         self.send_binding_acknowledgement()
#     def send_binding_acknowledgement(self, dst, src, sequence, status=0):
#         # Send a binding acknowledgment according to the parameters
#         ba = inet6.IPv6(dst= dst, src= src)/\
#                 inet6.MIP6MH_BA(status=status, seq=sequence)
#         p = Packet(self.iface, ba, 'Binding Acknowledgement', 'MIPv6')
#         self.iface.send(p, self.iface.mac)
#     
# class MIPv6Protocol(object):
#     #"""
#     #Mobile IPv6 (RFC 3775)
#     #"""
# 
#     def __init__(self, iface):
#         self.iface = iface
#         if self.iface.node.__class__ == HomeAgent:
#             self.mode = 'HA'
#             self.bindingCache = {} # An element of this dictionnary will be a dictionnary with all the information as follows :
#             # {MNHoA = {'MNCoA'=, 'Lifetime'=, 'HR'=1, 'maxSequenceNumber'=}}. Here, the dictionnary's key is the MNHoA.
#             # HR is a one bit flag indicating if this binding is a home registration or not. For us this is always the case
#             self.HAList = [] # If there is more than 1 HA on the Home link, each HA has to maintain a HA list with the following info :
#             # {'haLLIPAddr'=, 'globalIPAddrList'=, 'Lifetime'=, 'pref'=}
#         if self.iface.node.__class__ == MobileNode:
#             self.mode = 'MN'
#             self.HoA = self.iface.node.HoA
#             self.HAAddr = self.iface.node.HAaddr
#             self.bindingUpdateList = [] # An element of this list will be a dictionnary with all the informations as follows :
#             # {'HAAddr','HoA','CoA','InitLifetime'=,'RemainingLifetime'=,'maxSequenceNumber'=,'State'}
#             # State tells us if the entrey is valid or not
#         
# 
#     def handover(self):
#       # MN Handover
#   #TODO:
#   # - Look for new prefix AND if few RA are missed then we have moved
#   # - Delete default router
#   # - Send router solicitation
#   # - Receive RA so we can configure CoA
#   # - fast DAD
#   # - Binding Update 
#   
#   # - Delete default router
#   self.DefaultIPRouter = None
#         
#         self.received_ra = False
#         self.tentatives = []
#         self.ipv6.linklocal_addr = None
#         
#         
#         
#         self.configure_addr('FE80::'+ utils6.in6_mactoifaceid(self.iface.mac))
#         
#         for addr in self.addresses:
#             self.configure_addr(addr)
#         
#         self.register_mcast(self.all_nodes_mcast)
#         # Send a Router Sollicitations
#         self.router_solicitation_procedure(self.RSTransmits)
#   
#   
#   
#         # Delete th default router
#         self.DefaultIPRouter = None
# 
#         # Set the tentative address of the interface at the local link addres for the DAD
#         #self.iface.ipv6.icmpv6Protocol4Host.tentative_addr = 'FE80::'+ scapy.utils6.in6_mactoifaceid(self.iface.mac)
# 
#         # Send a NS for the DAD and wait to see if there is a response 
#         #self.iface.ipv6.icmpv6Protocol4Host.send_neighbor_solicitation_dad()
#         #self.iface.world.event(self.ICMPv6Protocol4Host.RetransTimer, self.iface.ipv6.icmpv6Protocol4Host.timeout_ns_dad)
# 
#         # Send a RS
#         #self.iface.ipv6.icmpv6Protocol4Host.send_router_solicitation('::')
# 
#         # TODO : Create CoA using prefix in the RA requested
# 
#         # Then, send a BU with the CoA created :
#         self.sendBU(CoA)
# 
# 
#     def send(self, node_addr, p, destination_addr):
#         '''node_addr is the address of the node calling the MIPv6 send method
#         p is either an IPv6 packet or a packet (TCP/UDP) coming from upper layer
#         destination_addr is the destination address of this sending'''
# 
#         if self.mode == 'HA':
#             #node_addr is here the HA address
#             #destination_addr is either the CN address or the MN address
#             
#             #Check if the destination is the CN or MN
#             if destination_addr.prefix == node_addr.prefix:
#                 #destination address is the MN's address
#                 #So it is a IPv6 packet coming from a CN via the HA
# 
#                 #Get the CoA from the BindingCache
#                 if destination_addr in self.bindingCache.keys():
#                     MNCoA = self.bindingCache[destination_addr]['MNCoA']
#                     create_tunnel(node_addr, packet, destination_addr, MNCoA)
#                 ###for index in len(self.bindingCache) :
#                 ## #   if self.bindingCache['MNHoA'] == 'destination_addr':
#                 ##  #      MNCoA = self.bindingCache[index]['MNCoA']
#                 #Encapsulate this packet into an tunnel IPv6
#             else:
#                 #destination address is the CN's address
#                 #packet is the IPv6 packet encapsulated in the tunnel from the MN
#                 self.iface.send(packet)
#                 
#         if self.mode == 'MN':
#             #node_addr is here the MN's address (CoA)
#             #destination_addr is the CN address (all the messages send to the HA have a specific methods)
#             
#             #We have consider that even for a CN on the visited network we will go through the HA to reach it
#             #If not use the following code:
#             ##if destination_addr.prefix == node_addr.prefix: 
#       #send the packet coming from upper layer normally with IPv6 header to a CN on the visited Network (kind of Routing Optimization)
#                 #p = inet6.IPv6(dst=daddr, src= naddr, hlim=255)/packet
#                 #self.iface.send(p)
#             ##else:
#                 #means that the destination is the CN via the HA
#       #get the HA address
#                 #HAaddr = BindingUpdateList[0]['HAAddr']
#       #send the packet
#                 #create_tunnel(node_addr, packet, destination_addr, HAaddr)
# 
#             #get the HA address
#             HAaddr = BindingUpdateList[0]['HAAddr']
#       #send the packet
#             create_tunnel(node_addr, packet, destination_addr, HAaddr)
# 
#     def create_tunnel(self, naddr, packet, daddr, taddr):
# 
#   #Is packet already an IPv6 packet
#   if packet[IPv6:1] :# If true the packet have an IPv6 Header otherwise it is a packet from the upper layer
#       sp = packet
#   else:
#       #create the IPv6 Header with the Node address and the destination address
#             sp = inet6.IPv6(dst=daddr, src= naddr, hlim=255)/packet
#         
#         #create an encapsulation of this IPv6 frame with
#         #tunneled address (taddr) as destination and Node address (naddr) as source
#         p = inet6.IPv6(dst=taddr, src= naddr, hlim=sp.chlim)/sp
#         #send the tunneled packet
#         self.iface.send(p)
# 
# 
#     def sendBU(self, CoA):
#         # Add the entry in the binding update list
#         self.bindingUpdateList[0]={'HAAddr' : self.HAAddr, 'HoA' :self.HoA, 'CoA' : CoA, 'maxSequenceNumber': 0, 'State':False}
#         # Compute the binding update message and send it
#         p = inet6.IPv6(dst= self.HAAddr, src= CoA)
#         p /= inet6.MIP6MH_BU(nh=60, flags='110000', seq=(self.bindingUpdateList[0]['maxSequenceNumber']+1) % 65536) 
#         p /= inet6.IPv6ExtHdrDestOpt(options[inet6.HAO(hoa=self.HoA)])
#         self.iface.send(p)
# 
#     def sendBA(self, dst, src, sequence, status=0):
#         # Send a binding acknowledgment according to the parameters
#         pkt = inet6.IPv6(dst= dst, src= src)/MIP6MH_BA(status=status, seq=sequence)
#         self.iface.send(pkt)
# 
#     def receiveData(self, packet):
#         # Check, if the node is a mobile node
#         if self.mode == 'MN':
#             # Check that the packet's source address is the MN's home agent one
#             if p.src == self.HAList[0]:
#                 # Recover the inner IPv6 packet and send it
#                 pkt = packet[IPv6:2]
#                 self.iface.node.dispatch(pkt, self.iface)
#         # Check, if the node is a home agent
#         if self.mode == 'HA':
#             # Check if the packet is a tunnel Ipv6/Ipv6
#             if packet[IPv6:1].nh == 41:
#                 # Check that the source address of the inner IPv6 header is in its binding cache
#                 if packet[IPv6:2].src in self.bindingCache.keys():
#                     pkt = packet[IPv6:2]
#                     self.send(self.HAAddr, pkt, pkt.dst)
#                 else :
#                     # Directly call the send function
#                     self.send(self.iface.node.HAaddr, packet, p.dst)
# 
#     def receiveBinding(self, packet):
#         # Check if the node is a MN
#         if self.mode == 'MN':
#             # Check if the source address is the one of the MN's HA
#             if p.src == self.HAList[0] :
#                 # Check if the message is a binding acknowledgement
#                 if p.mhtype == 'BA' :
#                     # Recover informations in the BA
#                     CoA = p.dst
#                     LifeTime = p.mhtime
#                     Sequence = p.seq
#                     Status = p.status
#                     # Update the binding update list
#                     if Sequence == self.bindingUpdateList[0]['Sequence']:
#                         if Status == 0:
#                             self.bindingUpdateList[0]['RemainingLifetime'] = LifeTime
#                             self.bindingUpdateList[0]['State'] = True
# 
#                     else:
#                         # Discard the message
#                         pass
#             else:
#                 #Discard the packet
#                 pass
# 
#         # Check if the node is a HA
#         if self.mode == 'HA':
#             # Check if the message is a binding update
#             if p.mhtype == 'BU': # TODO : Check somewhere that the bit 'HR' is set to 1
#                 # Recover informations about the BU
#                 CoA = p.src
#                 HoA = p.hoa
#                 LifeTime = p.mhtime
#                 Sequence = p.seq
#                 # Check that the Home Address Option is in the packet
#                 if p.hoa : # TODO : Check that the HoA in the option is a unicast address and an 
#                                 # on-link IPv6 @ with respect to the home agent's current Prefix List
#                     # Check that it manages this HoA
#                     if HoA in self.bindingCache.keys():
#                         # Check that the sequence number in the BU is greater than the one in the last BU for this HoA
#                         if (self.bindingCache[index]['maxSequenceNumber'] < Sequence): # TODO : modulo 65536
#                             # Filter on the LifeTime to delete or update an entry
#                             if LifeTime != 0:
#                                 # Update the entry
#                                 self.bindingCache[HoA] = {'MNCoA':CoA, 'Lifetime':LifeTime, 'HR':1, 'maxSequenceNumber': Sequence}
#                                 # Send a binding acknowledgement
#                                 sendBA(CoA, self.ipv6_adresses[0],Sequence)
#                             else:
#                                 # Delete the entry
#                                 del self.bindingCache[HoA]
#                         # The entry doesn't exist yet in the bindig cache
#                         else:
#                             # TODO : perform DAD on the link for the HoA
#                             if not response: # If no response to DAD
#                                 # Add the entry in the binding cache
#                                 self.bindingCache[HoA]={'MNCoA':CoA, 'Lifetime':LifeTime, 'HR':1, 'maxSequenceNumber': Sequence}
#                                 # Send a BA
#                                 sendBA(CoA,self.ipv6_adresses[0],Sequence)
#                             else:
#                                 # Send a BA with error type : DAD error
#                                 sendBA(CoA, self.ipv6_adresses[0],status=134, sequence = Sequence)
#                 else:
#                     # Discard the message
#                     pass
#             elif p.mhtype == 'BA':
#                 # Discard the message
#                 pass
