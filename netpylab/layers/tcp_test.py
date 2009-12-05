"""
Tests for TCP state machine for scapy.
 
On mac OS X you need to set the machine to drop Rst packets with the following
command: 

>>> sudo ipfw add 00042 drop tcp from any to any in tcpflags rst src-port any

Special thanks to Cash, Robin, and the rest of the crew on scapy-dev

:author: 
    Adam Pridgen <adam.pridgen@thecoverofnight.com>

:copyright:
    Copyright 2009 Adam Pridgen <adam.pridgen@thecoverofnight.com>

    This program is free software; you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by the Free
    Software Foundation; either version 3, or (at your option) any later
    version.

    This program is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
    FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
    more details.

    You should have received a copy of the GNU General Public License along
    with this program; see the file COPYING.  If not, write to the Free
    Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
    02110-1301, USA.
"""
from tcp import *


def setup_tcp_connection(dst, dport, sport):
	f = TCPState()
	base_pkt = f.build_basic_pkt(dst, dport, sport)
	rpkt,result = f.establish_connection(base_pkt)
	if not result:
		print "Failed to get a successful SA"
		return None
	return f


def listen_tcp_connection(port):
	f = TCPState()
	rpkt, result = f.listen(port)
	if not result:
		print "Failed to get a successful connection"
		return None
	return f


rpkt = listen_tcp_connection(9000) 