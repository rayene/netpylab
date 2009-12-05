#!/usr/bin/env python
# encoding: utf-8
"""
sockets.py

Created by Rayene on 2009-03-05.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""
from scapy.layers import inet, inet6
from packets import Packet

IPV4 = 4
IPV6 = 6
# UDP = 0
# TCP = 1



class VirtSocket(object):
    def __init__(self, app, receive_func, family, proto, dst_ip, dst_port, src_port=None, iface = None):
        self.app = app
        self.node = self.app.node
        self.family = family # IPV4 or IPV6
        self.proto = proto
        self.dst_ip = dst_ip
        self.iface = iface
        
        if family == IPV4:
            self.node_send = self.node.route_ipv4
            self.p_data = inet.IP(dst=dst_ip)
            self.f = inet.IP
            
        elif family == IPV6:
            self.node_send = self.node.route_ipv6
            self.p_data = inet6.IPv6(dst=dst_ip)
            self.f = inet6.IPv6
        
        self.src_port  = src_port 
        
        self.p_data /= proto(dport=dst_port)
        self.receive_func = receive_func
        
    def register_receiver(self):
        if self.receive_func:
            self.src_port = self.node.register(self, self.f, self.proto, self.src_port)
            self.p_data.sport = self.src_port
            return self.src_port
    
    def open(self):

        if not self.dst_ip and self.receive_func: 
            return self.register_receiver()
        if self.family == IPV4:
            self.p_data.src = str(self.node.which_ipv4_src_address(self.dst_ip))
        elif self.family == IPV6:
            src = self.node.which_ipv6_src_address(self.dst_ip, self.iface)
            if src and self.register_receiver():
                self.p_data.src = str(src)
                return True
        return False

                


            
    def close(self):
        print 'CLOSING'
        if self.receive_func:
            self.node.unregister(self.f, self.proto, self.src_port)
    
    def send(self, data, dst_addr = None, dst_port = None):
        if dst_addr: 
            self.p_data.dst = dst_addr
            src_addr = self.node.which_ipv6_src_address(dst_addr)
            if not src_addr:
                self.app.add_to_history('No Source Address')
                return 
            self.p_data.src = str(src_addr)
        if dst_port: self.p_data.dport = dst_port
        p = Packet(self.app, self.p_data/data, 'Application Data', 'AppData')
        
        self.app.add_to_history('Packet Sent', p)
        self.node_send(p, self.iface)
    
    def receive(self, p):
        self.receive_func(p)