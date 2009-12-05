#!/usr/bin/env python
# encoding: utf-8
"""
channels.py

Created by Rayene on 2009-01-31.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""

# Different link layers have different properties.  The ones of concern 
#    to Neighbor Discovery are: 
#    multicast      - a link that supports a native mechanism at the 
#                     link layer for sending packets to all (i.e., 
#                     broadcast) or a subset of all neighbors. 
#    point-to-point - a link that connects exactly two interfaces.  A 
#                     point-to-point link is assumed to have multicast 
#                     capability and have a link-local address. 
#    non-broadcast multi-access (NBMA) 
#                   - a link to which more than two interfaces can attach, 
#                     but that does not support a native form of multicast 
#                     or broadcast (e.g., X.25, ATM, frame relay, etc.). 
# source: rfc2461
#----------------------------------------------------------------------

class Channel(object):
    
    def __init__(self, world):
        self.interfaces = []
        
    def register(self, new_iface):
        for iface in self.interfaces:
            iface.reachable[new_iface] = self.__class__.REACHABILITY
            new_iface.reachable[iface] = self.__class__.REACHABILITY
        self.interfaces.append(new_iface)
        
    def unregister(self, iface):
        self.interfaces.remove(iface)
    

class EthernetCable(Channel):
    REACHABILITY = True

class WiFiChannel(Channel):
    REACHABILITY = False

class WiMaxChannel(Channel):
    REACHABILITY = False

def init_wireless_channels(world):
    WiFiChannel.channel = WiFiChannel(world)
    WiMaxChannel.channel = WiMaxChannel(world)
    