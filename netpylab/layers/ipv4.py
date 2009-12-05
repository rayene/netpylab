#!/usr/bin/env python
# encoding: utf-8
"""
ipv4.py

Created by Rayene on 2009-02-27.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""

# import scapy.utils6
# from scapy.layers import inet
# import socket
from packets import Packet

class ArpProtocol(object):
#TODO: Gratuitous ARP
    def __init__(self, iface):
        self.iface = iface
        self.table={}
        self.waiting={}
    
    def start(self):
        pass
    
    def stop(self):
        # TODO: kill timers here
        pass
    
    def send(self, p):
        ipv4_addr = p.dst
        if self.table.has_key(ipv4_addr):
            
            self.iface.send(p, self.table[ipv4_addr])
        elif self.waiting.has_key(ipv4_addr):
                self.waiting[ipv4_addr].append(p)
        else: # address not in ARP table and no pending request
            arp_p = Packet(self.iface,
                    l2.ARP(pdst=ipv4_addr, psrc=self.iface.ipv4_addresses[0][0],
                    hwsrc=self.iface.mac),
                    "ARP Request", "ARP")
            #print 'sent ARP : ', arp_p.summary(), self.iface.label
            self.iface.send(arp_p, ETHER_BROADCAST)
            self.waiting[ipv4_addr]=[p]
            #TODO, implement timeout
        return None
    
    def receive(self, p):
        #print 'received ARP: ', p.summary(), self.iface.label
        if p.op == 2: # ARP is-at
            self.table[p.psrc] = p.hwsrc
            if p.psrc in self.waiting:
                for waiting_p in self.waiting[p.psrc]:
                    #print "--"*20, waiting_p.summary()
                    self.send(waiting_p), #, p.hwsrc
                del(self.waiting[p.psrc])
        elif p.op == 1: # ARP who-has
            self.table[p.psrc]=p.hwsrc
            resp = Packet(self.iface,
                        l2.ARP(op='is-at', hwsrc = self.iface.mac,
                        psrc=self.iface.ipv4_addresses[0][0],
                        hwdst=p.hwsrc, pdst= p.psrc),
                        "ARP Response", "ARP")
            self.iface.send(resp, p.hwsrc)
        else:
            assert False

  

class Route4:
    def __init__(self, interfaces):
        self.interfaces = interfaces
        self.resync()
        self.cache = {}

    def invalidate_cache(self):
        self.cache = {}

    def resync(self):
        self.invalidate_cache()
        self.routes = []
        for iface in self.interfaces:
            if len(iface.ipv4_addresses) > 0:
                self.ifadd(iface, iface.ipv4_addresses[0][0]+'/'+str(iface.ipv4_addresses[0][1]))

    def __repr__(self):
        rt = "Network         Netmask         Gateway         Iface           Output IP\n"
        for net,msk,gw,iface,addr in self.routes:
            rt += "%-15s %-15s %-15s %-15s %-15s\n" % (ltoa(net),
                                              ltoa(msk),
                                              gw,
                                              iface,
                                              addr)
        return rt

    def make_route(self, host=None, net=None, gw=None, dev=None):
        if host is not None:
            thenet,msk = host,32
        elif net is not None:
            thenet,msk = net.split("/")
            msk = int(msk)
        else:
            raise Scapy_Exception("make_route: Incorrect parameters. You should specify a host or a net")
        if gw is None:
            gw="0.0.0.0"
        if dev is None:
            if gw:
                nhop = gw
            else:
                nhop = thenet
            dev,ifaddr,x = self.route(nhop)
        else:
            ifaddr = get_if_addr(dev)
        return (atol(thenet), itom(msk), gw, dev, ifaddr)

    def add(self, *args, **kargs):
        """Ex:
        add(net="192.168.1.0/24",gw="1.2.3.4")
        """
        self.invalidate_cache()
        self.routes.append(self.make_route(*args,**kargs))

        
    def delt(self,  *args, **kargs):
        """delt(host|net, gw|dev)"""
        self.invalidate_cache()
        route = self.make_route(*args,**kargs)
        try:
            i=self.routes.index(route)
            del(self.routes[i])
        except ValueError:
            self.iface.world.log.warning("no matching route found")
             
    def ifchange(self, iff, addr):
        self.invalidate_cache()
        the_addr,the_msk = (addr.split("/")+["32"])[:2]
        the_msk = itom(int(the_msk))
        the_rawaddr = atol(the_addr)
        the_net = the_rawaddr & the_msk
        
        
        for i in range(len(self.routes)):
            net,msk,gw,iface,addr = self.routes[i]
            if iface != iff:
                continue
            if gw == '0.0.0.0':
                self.routes[i] = (the_net,the_msk,gw,iface,the_addr)
            else:
                self.routes[i] = (net,msk,gw,iface,the_addr)
        #netcache.flush()
        
                

    def ifdel(self, iff):
        self.invalidate_cache()
        new_routes=[]
        for rt in self.routes:
            if rt[3] != iff:
                new_routes.append(rt)
        self.routes=new_routes
        
    def ifadd(self, iff, addr):
        self.invalidate_cache()
        the_addr,the_msk = (addr.split("/")+["32"])[:2]
        the_msk = itom(int(the_msk))
        the_rawaddr = atol(the_addr)
        the_net = the_rawaddr & the_msk
        self.routes.append((the_net,the_msk,'0.0.0.0',iff,the_addr))


    def route(self,dest,verbose=None):
        if dest in self.cache:
            return self.cache[dest]
        dst = atol(dest)
        pathes=[]
        for d,m,gw,i,a in self.routes:
            aa = atol(a)
            if aa == dst:
                pathes.append((0xffffffffL,(LOOPBACK_NAME,a,"0.0.0.0")))
            if (dst & m) == (d & m):
                pathes.append((m,(i,a,gw)))
        if not pathes:
            return None

        # Choose the more specific route (greatest netmask).
        # XXX: we don't care about metrics
        pathes.sort()
        ret = pathes[-1][1]
        self.cache[dest] = ret
        return ret
            
    def get_if_bcast(self, iff):
        for net, msk, gw, iface, addr in self.routes:
            if (iff == iface and net != 0L):
                bcast = atol(addr)|(~msk&0xffffffffL); # FIXME: check error in atol()
                return ltoa(bcast);
        self.iface.world.log.warning("No broadcast address found for iface %s\n" % iff);

      