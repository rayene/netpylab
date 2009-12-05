#!/usr/bin/env python
# encoding: utf-8
"""
sockets.py

Created by Rayene on 2009-03-05.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""
from layers import tcp
from scapy.layers import inet, inet6
# from packets import Packet



SOCK_STREAM = inet.TCP
SOCK_DGRAM = inet.UDP

AF_INET = inet.IP
AF_INET6 = inet6.IPv6


class socket(object):
    def __init__(self, application, family = AF_INET, type = SOCK_STREAM, proto = 0):
        """This module imitates the python socket API. This is intended to
        facilitate porting python applications using sockets into NetPyLab.
        
        Below you can find the documentation for the original socket object:
        
        Create a new socket using the given address family, socket
        type and protocol number. The address family should be AF_INET
        (the default), AF_INET6 or AF_UNIX. The socket type should be
        SOCK_STREAM (the default), SOCK_DGRAM or perhaps one of the other
        SOCK_ constants. The protocol number is usually zero and
        may be omitted in that case."""
        self.application = application
        self.node = application.node
        if family not in (AF_INET, AF_INET6):
            raise RuntimeError('Protocol family %d not supported' % family)
        self.family = family
        
        if type not in (SOCK_DGRAM, SOCK_STREAM):
            raise RuntimeError('Protocol type %d not supported' % type)
        self.type = type
        
        if self.type == SOCK_DGRAM:
            pass
        else:
            self.tcp = tcp.TCPState(self)
            self.databuf = ''
            self.udatabuf = ''
            self.port = 0
            self.accepted = 0
            self.listening = 0
        
    def accept(self):
            if not self.listening:
                    raise RuntimeError('Socket is not listening')
            self.listening = 0
            self.tcp.listen()
            self.accepted = 1
            return self, self.getsockname()
    
    def bind(self, address):
            self.host, self.port = address
    
    def close(self):
        if self.accepted:
            self.accepted = 0
            return
        self.tcp.Abort()
    
    def connect(self, address):
        self.d_addr, self.d_port = address
        self.s_port = self.node.register(self, self.family, SOCK_STREAM)
        
        self.s_addr = self.node.which_ipv6_src_address(self.d_addr)
        self.tcp.establish_connection() #ActiveOpen(self.port, _ipaddress(host), port)
    
    def getsockname(self):
             host, port = self.tcp.GetSockName()
             host = macdnr.AddrToStr(host)
             return host, port
    
    def getpeername(self):
             st = self.tcp.Status()
             host = macdnr.AddrToStr(st.remoteHost)
             return host, st.remotePort
    
    def listen(self, backlog):
            self.tcp.PassiveOpen(self.port)
            self.listening = 1
    
    def makefile(self, rw = 'r', bs = 512):
            return _socketfile(self, rw, bs)
    
    def recv(self, bufsize, flags=0):
            if flags:
                    raise RuntimeError('recv flags not yet supported')
            if not self.databuf:
                    try:
                            self.databuf, urg, mark = self.tcp.Rcv(0)
                    except mactcp.error, arg:
                            if arg[0] != MACTCP.connectionClosing:
                                    raise mactcp.error, arg
            rv = self.databuf[:bufsize]
            self.databuf = self.databuf[bufsize:]
            return rv
    
    def send(self, buf):
            self.tcp.Send(buf)
            return len(buf)
    
    def shutdown(self, how):
            if how == 0:
                    return
            self.tcp.Close()
    
    def bytes_readable(self):
            st = self.tcp.Status()
            return st.amtUnreadData
    
    def bytes_writeable(self):
            st = self.tcp.Status()
            return st.sendWindow - st.sendUnacked;

    def send_to_IP(self, pkt):
        self.node_send(pkt, self.iface)
# 
# 
# 
# class VirtSocket(object):
#     def __init__(self, app, receive_func, family, proto, dst_ip, dst_port, src_port=None, iface = None):
#         self.app = app
#         self.node = self.app.node
#         self.family = family # IPV4 or IPV6
#         self.proto = proto
#         self.dst_ip = dst_ip
#         self.iface = iface
#         
#         if family == IPV4:
#             self.node_send = self.node.route_ipv4
#             self.p_data = inet.IP(dst=dst_ip)
#             self.f = inet.IP
#         
#         elif family == IPV6:
#             self.node_send = self.node.route_ipv6
#             self.p_data = inet6.IPv6(dst=dst_ip)
#             self.f = inet6.IPv6
#         
#         self.src_port  = src_port
#         
#         self.p_data /= proto(dport=dst_port)
#         self.receive_func = receive_func
#     
#     def register_receiver(self):
#         if self.receive_func:
#             self.src_port = self.node.register(self, self.f, self.proto, self.src_port)
#             self.p_data.sport = self.src_port
#             return self.src_port
#     
#     def open(self):
#         
#         if not self.dst_ip and self.receive_func:
#             return self.register_receiver()
#         if self.family == IPV4:
#             self.p_data.src = str(self.node.which_ipv4_src_address(self.dst_ip))
#         elif self.family == IPV6:
#             src = self.node.which_ipv6_src_address(self.dst_ip, self.iface)
#             if src and self.register_receiver():
#                 self.p_data.src = str(src)
#                 return True
#         return False
# 
# 
#     def close(self):
#         print 'CLOSING'
#         if self.receive_func:
#             self.node.unregister(self.f, self.proto, self.src_port)
#     
#     def send(self, data, dst_addr = None, dst_port = None):
#         if dst_addr:
#             self.p_data.dst = dst_addr
#             src_addr = self.node.which_ipv6_src_address(dst_addr)
#             if not src_addr:
#                 self.app.add_to_history('No Source Address')
#                 return
#             self.p_data.src = str(src_addr)
#         if dst_port: self.p_data.dport = dst_port
#         p = Packet(self.app, self.p_data/data, 'Application Data', 'AppData')
#         
#         self.app.add_to_history('Packet Sent', p)
#         self.node_send(p, self.iface)
#     
#     def receive(self, p):
#         self.receive_func(p)