"""
TCP state machine for scapy.

Special thanks to Robert "Bob" Grant <robert.david.grant@gmail.com> for help
with the TCP sliding window algorithm and comments.

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
    
:var MAX:
    Maximum sequence number
"""
# import scapy.layers.inet
from random import randint

MAX = 2 ** 32 - 1


class snd:
    '''
    TCP SND object.  Reference RFC 793.  TCP not fully implemented.
    '''
    
    def __init__(self):
        self.UNA = randint(0, 65535) # send unacknowledged
        self.NXT = self.UNA + 1 # send next
        self.WND = 8192 # send window
        self.UP = 0 # send urgent pointer
        self.WL1 = 0 # segment sequence number used for last window update
        self.WL2 = 0 # segment acknowledgment number used for last window update
        self.ISS = self.UNA + 1# initial send sequence number
    
    
    def init_from_rcv_seg(self, seg):
        '''
        Set the default seq number based on a segment.
        '''
        self.ISS = seg.ack
        self.NXT = seg.ack
        self.UNA = self.NXT - 1
        self.WND = seg.window
        self.WL2 = seg.seq
        self.WL1 = seg.ack
    
    def init_from_seg(self, seg):
        self.init_from_snd_seg(seg)
    
    def init_from_snd_seg(self, seg):
        '''
        Set the default seq number based on a segment.
        '''
        self.ISS = seg.seq
        self.NXT = seg.seq
        self.UNA = self.NXT -1 
        self.WND = seg.window
        self.WL2 = seg.ack
        self.WL1 = seg.seq

    
    def get_nxt_seq(self):
        '''
        Get the next valid seq number.

        :return: next sequence number
        :rtype: int
        '''
        return self.NXT
    
    def can_send_data(self):
        '''
        Determine if data can be sent at this time by checking the current
        window.

        :return: data can be sent
        :rtype: boolean
            
        '''
        if self.UNA > self.NXT:
            return ((self.NXT + MAX) - self.UNA) % MAX < WND
        return (self.NXT - self.UNA) < WND
    
    def is_acceptable_ack(self, ack):
        '''
        Check the ack to see if it is valid.

        :return: ack is valid
        :rtype: boolean
        '''
        print self
        print self.UNA + self.WND, self.UNA, (self.UNA + self.WND) % MAX
         
        UPP = (self.UNA + self.WND) % MAX
        LOW = self.UNA
        is_valid = False
        if LOW <= UPP:
            is_valid = LOW <= ack < UPP
            print "LOW: %d < ack: %d < UPP: %d"%(LOW, ack, UPP)
        else:
            if ack < LOW:
                is_valid = LOW <= ack + MAX < UPP + MAX
                print "LOW: %d < ack: %d < UPP: %d"%(LOW, ack+MAX, UPP+MAX)
            else:
                is_valid = LOW <= ack < UPP + MAX
                print "LOW: %d < ack: %d < UPP: %d"%(LOW, ack, UPP+MAX)
        return is_valid
    
    def update_una(self, ack):
        '''
        Update the un-acked segments to the current ack number.

        :param ack: current ack number
        :type ack: int

        :return: ack is valid
        :rtype: boolean
        '''
        self.UNA = (self.UNA + ack) % MAX
    
    def rcv_seg(self, seg):
        '''
        Check the current segment to see if its valid, then 
        update the sliding window (e.g. NXT & UNA)

        :param seg: current segment
        :type seg: scapy.TCP

        :return: state successfully updated
        :rtype: boolean
        '''
        
        print "Segment ack: ",self.is_acceptable_ack(seg.ack), "\n", repr(seg)
        if self.is_acceptable_ack(seg.ack):
            ack_wnd = self.get_ack_wnd(seg.ack)
            self.update_una(ack_wnd)
            return True
        return False
    
    def update_from_seg(self, pkt):
        '''
        Check the current pkt to see if its valid, then update the sliding
        window (e.g. NXT & UNA) if the ack is valid.

        :param pkt: packet to update TCP SND state from 
        :type pkt: scapy.Packet

        :return: state successfully updated
        :rtype: boolean
        '''
        if not TCP in pkt: return False
        return self.rcv_seg(pkt[TCP])
        
    def update_seg(self, seg, p_load=None):
        '''
        Update the segment in accordance to the sliding window Returns a tuple
        of the segment and any unused payload.  If a valid segment CAN NOT be
        sent then the returned seg is None.

        :param seg: segment to update 
        :type seg: scapy.Packet
        :param p_load: payload to include in the packet
        :type p_load: string

        :return: (segment if one was created, Otherwise None, unused payload data)
        :rtype: tuple
        '''
        payload = ""
        #seg.show()
        if not p_load is None:
            payload = p_load
            p_load = None
        else:
            payload = str(seg.payload)
        
        wnd_sz = self.get_current_wnd_sz()
        print "Calculated a wnd_sz of %x" % wnd_sz
        if wnd_sz <= 0:
            return None, payload
        
        
        data_len = self.get_payload_len(payload, wnd_sz)
        seg.seq = self.NXT
        self.update_nxt(data_len + 1)
        if payload != '':
            seg.payload = payload
        if len(payload) > data_len:
            seg.payload = payload[:data_len]
            return seg, payload[data_len:]
        return seg, ""

    def force_update_seg(self, seg, p_load=None):
        '''
        Update the segment in accordance to the sliding window Returns a tuple
        of the segment and any unused payload.  If a valid segment CAN NOT be
        sent then the returned seg is None.

        :param seg: segment to update 
        :type seg: scapy.Packet
        :param p_load: payload to include in the packet
        :type p_load: string

        :return: (segment if one was created, Otherwise None, unused payload
                 data)
        :rtype: tuple
        '''
        payload = ""
        if not p_load is None:
            payload = p_load
            p_load = None
        else:
            payload = str(seg.payload)
        wnd_sz = self.get_current_wnd_sz()
        print "Calculated a wnd_sz of %x" % wnd_sz
        
        data_len = self.get_payload_len(payload, wnd_sz)
        seg.seq = self.NXT
        self.update_nxt(data_len + 1)
        if payload != '':
            seg.payload = payload
        if len(payload) > data_len:
            seg.payload = payload[:data_len]
            return seg, payload[data_len:]
        return seg, ""

    
    def get_payload_len(self, payload, rem_sz=None):
        '''
        Get the packet length with the payload.

        :param payload: payload to be sent in the segment
        :type payload: string
        :param rem_sz: remaining size in the sliding window
        :type rem_sz: int or None

        :return: the value of the next sequence number after the segment is
                 sent
        :rtype: int
        '''
        wnd_sz = 0
        if not rem_sz is None:
            wnd_sz = rem_sz
            rem_sz = None
        else: 
            wnd_sz = self.get_current_wnd_sz()
        if len(payload) > wnd_sz:
            return wnd_sz
        return len(payload)
        
    def get_current_wnd_sz(self):
        '''
        Get the remaining window size for sending packet data.

        :return: remaining data that can be sent in the window
        :rtype: int 
        '''
        wnd_used = abs(self.NXT - self.UNA)
        if self.UNA > self.NXT:
            wnd_used = abs((self.NXT + MAX) - self.UNA) % MAX
        return self.WND - wnd_used

    def get_ack_wnd(self, ack):
        '''
        Get the window that corresponds to the ack number.

        :param ack: ack to obtain the update window from
        :type ack: int

        :return: window of data to be ack'ed
        :rtype: int
        '''
        ack_wnd = abs(self.UNA - ack)
        if ack >= self.UNA:
            ack_wnd = abs(self.UNA + MAX - ack) % MAX
        return ack_wnd
    
    def set_wnd(self, wnd):
        '''
        Set the sliding window size.

        :param wnd: new sliding window size
        :type wnd: int
        '''
        self.WND = wnd
            
    def update_nxt(self, incr):
        '''
        Update the NXT valid seq number after data after prep'ing a segment.

        :param incr:  increment the NXT by the previous segment size
        :type incr: int
        '''
        self.NXT = (self.NXT + incr) % MAX
    
    def __str__(self):
        s = "SND Object values\n"
        s += "UNA: %d \n"%self.UNA 
        s += "NXT: %d \n"%self.NXT 
        s += "WND: %d \n"%self.WND 
        s += "UP: %d \n"%self.UP 
        s += "WL1: %d \n"%self.WL1 
        s += "WL2: %d \n"%self.WL2 
        s += "ISS: %d \n"%self.ISS 
        return s
        

class rcv:
    '''
    TCP RCV object.  Reference RFC 793.  TCP not fully implemented.
    '''

    def __init__(self):
        self.NXT = randint(0, 65535) # receive next
        self.WND = 0 # receive window
        self.UP = 0 # receive urgent pointer
        self.IRS = self.NXT # initial receive sequence number
        self.rcvd_segs = {}
    
    def init_from_seg(self, seg):
        '''
        Set the default seq number based on a rcvd syn-ack segment.
        '''
        self.init_from_rcv_seg(seg)

    def init_from_snd_seg(self, seg):
        '''
        Set the default seq number based on a rcvd syn-ack segment.
        '''
        self.WND = seg.window
        self.IRS = seg.ack
        self.NXT = (seg.ack) % MAX
    
    def init_from_rcv_seg(self, seg):
        '''
        Set the default seq number based on a rcvd syn-ack segment.
        '''
        self.WND = seg.window
        self.IRS = seg.seq
        self.NXT = (seg.seq) % MAX

    def init_from_seg(self, seg):
        self.init_from_rcv_seg(seg)

    def update_nxt(self, incr):
        '''
        Update the NXT valid ack number after sending an ack.

        :param incr:  Increment the NXT by the previous segment size.
        :type incr: int
        '''
        self.NXT = (self.NXT + incr) % MAX
    
    def rcv_seg(self, seg):
        '''
        Check the current segment to see if its valid, then 
        update the sliding window (e.g. NXT)

        :param seg: current segment
        :type seg: scapy.TCP

        :return: state successfully updated
        :rtype: boolean
        '''
        if self.is_acceptable_seq(seg.seq, len(seg.payload)+1):
            self.rcvd_segs[seg.seq] = seg
            if self.NXT != seg.seq:
                return False
            return self.accumulate_acks()
        return False
        
    def accumulate_acks(self):
        '''
        Accumulate saved segments, this will need to be changed if RT Timers
        are used.

        :return: updated ack window
        :rtype: boolean
        '''
        rcvd_seqs = self.rcvd_segs.keys()
        rcvd_seqs.sort()
        flag = False
        for i in rcvd_seqs:
            seg = self.rcvd_segs[i]
            if seg.seq == self.NXT:
                incr = len(str(seg.payload)) + 1
                self.update_nxt(incr)
                del self.rcvd_segs[i]
                flag = True
            else:
                break
        return flag
    
    def update_seg(self, seg):
        '''
        Update the segment in accordance to the sliding window
        Returns a tuple of the segment and any unused payload.  If
        a valid segment CAN NOT be sent then the returned seg is None.

        :param seg: segment to update 
        :type seg: scapy.Packet

        :return: (segment if one was created, Otherwise None, unused payload data)
        :rtype: tuple
        '''
        seg.ack = self.get_nxt_ack()
        
        return seg, None
    
    def get_last_ack(self):
        '''
        Return current last ack value sent.

        :return: current ack number or seq number we are waiting for  
        :rtype: int
        '''
        return self.NXT - 1
    
    def get_nxt_ack(self):
        '''
        Return current ack Number.

        :return: current ack number or seq number we are waiting for  
        :rtype: int
        '''
        return self.NXT

        
    def update_from_seg(self, pkt):
        '''
        Check the current pkt to see if its valid, then 
        update the sliding window (e.g. NXT & UNA) if the 
        ack is valid.

        :param pkt: packet to update TCP SND state from 
        :type pkt: scapy.Packet

        :return: state successfully updated
        :rtype: boolean
        '''
        
        if not TCP in pkt: return
        self.rcv_seg(pkt[TCP])
            
    def set_wnd(self, wnd):
        '''
        Set the TCP window.

        :param wnd: new window to set the RCV too
        :type wnd: int
        '''
        self.WND = wnd

    def is_acceptable_seq(self, seq, seg_sz):
        '''
        Check the seq to see if it is valid.

        :return: seq is valid
        :rtype: boolean
        '''
        UPP = (self.NXT + self.WND) % MAX
        LOW = self.NXT % MAX
        is_valid = False
        print "seq: %d LOW: %d UPP: %d"%(seq, LOW, UPP)
        if LOW <= UPP:
            is_valid = LOW <= seq + seg_sz < UPP
            print "LOW: %d  <= seq + seg_sz: %d  < UPP: %d == %s"%(LOW, seq+seg_sz, UPP, str(is_valid))
        else:
            if seq < LOW:
                is_valid = LOW <= seq + seg_sz + MAX < UPP + MAX
                print "LOW: %d  <= seq + seg_sz + MAX: %d  < UPP: %d == %s"%(LOW, seq+seg_sz+MAX, UPP+MAX, str(is_valid))
            else:
                is_valid = LOW <= seq + seg_sz < UPP + MAX
                print "LOW: %d  <= seq + seg_sz: %d  < UPP: %d == %s"%(LOW, seq+seg_sz, UPP+MAX, str(is_valid))
        return is_valid
    
    def __str__(self):
        s = "RCV Object values\n"
        s += "NXT: %d \n"%self.NXT 
        s += "WND: %d \n"%self.WND 
        s += "UP: %d \n"%self.UP 
        s += "IRS: %d \n"%self.IRS
        f = self.rcvd_segs.keys()
        f.sort()
        k = lambda num: str(num)
        s += "rcvd_segs: %s \n"%",".join(map(k, f)) 
        return s


#@conf.commands.register
class TCPState(object):
    '''
    Basic implementation of the TCP State Machine (SM) that 
    is meant to work with scapy.

    Reference RFC 793.  TCP not fully implemented.  This installment gives
    no attention to timers, congestion windows, etc.  This is a basic protocol
    implementation so that we can talk to our estranged partner host.
    '''
    flag_vals = {"F":0x1, "S":0x2, "R":0x4, "P":0x8,
                  "A":0x10, "U":0x20, "E":0x40, "C":0x80 }
    
    def __init__(self, socket):
        self.socket = socket
        # RCV should actually be initialized when the 
        # 3-way hand shake takes place
        irs = randint(0, 0x0FFFFFFFF)
        iss = randint(0, 0x0FFFFFFFF)
        print "Initializing the SND with %x and RCV with %x" % (iss, irs)
        self.SND = snd()
        self.RCV = rcv()
        self.seg_record = []# keep record of session  
        self.una_segs = []    # maintain list of un-acked segs
        self.previous_payload = None # for ans TCP data send
        self.state = "CLOSED"
        self.sock = None
        self.move_state = self.state_closed
        # TCP segment info
        self.sport = randint(0, 0x0FFFFFFFF)
        self.dport = randint(0, 0x0FFFFFFFF)
        self.dst = 'localhost'
         
    def get_socket(self, s):
        if not s is None:
            self.sock = s
            s = None
        elif s is None and self.sock is None:
            self.sock = self.init_socket()
    
    def get_pkt(self, pkt):
        p = pkt
        if p is None:
            p = self.get_base_pkt()
        return p

    def add_ether(self, pkt):
        if Ether not in pkt:
            return Ether() / pkt
        return pkt
    
    def check_flags(self, seg, flag_str):
        '''
        Compare segment flag values to a flag string.

        :param seg: segment to compare flag values 
        :type seg:  scapy.TCP
        :param flag_str: flag string to compare against the 
        :type flag_str:  string
                         segment
        :return: flag values match 
        :rtype: boolean
        '''
        return self.get_flag_val(flag_str) == seg.flags
    
    def init_from_pkt(self, seg):
        '''
        Initialize the TCP SM based on a TCP segment.

        :param seg: segment to initialize SM from 
        :type seg:  scapy.TCP
        '''        
        self.RCV.init_from_seg(seg)
        self.SND.init_from_seg(seg)
        
        
        
    def get_rbase_tcp(self, rseg):
        '''
        Creates a base TCP segment based on a rcvd segment.

        :param rseg: rcvd segment to base a new segment off of 
        :type rseg:  scapy.TCP
        '''
        sport = rseg.dport
        dport = rseg.sport
        options = rseg.options
        return TCP(sport=sport, dport=dport, options=options)
    
    def get_rbase_ip(self, rpkt):
        '''
        Creates a base IP packet based on a rcvd segment.

        :param rpkt: rcvd IP packet to base a new packet off of 
        :type rpkt:  scapy.IP
        '''        
        dst = rpkt.src
        src = rpkt.dst
        options = rpkt.options
        return IP(src=src, dst=dst, options=options)
    
    def get_rbase_pkt(self, rpkt):
        '''
        Creates a base packet based on a rcvd packet.

        :param rpkt: rcvd segment to base a new packet off of 
        :type rpkt:  scapy.IP/scapy.TCP
        '''
        return IP(dst=rpkt[IP].src) / TCP(dport=rpkt[TCP].sport, sport=rpkt[TCP].dport)

    def get_base_tcp(self):
        '''
        Creates a base TCP segment based on a defined internal TCP parameters
        segment.
        '''
        sport = self.sport
        dport = self.dport
        return TCP(sport=sport, dport=dport)
    
    def get_base_ip(self):
        '''
        Creates a base IP packet based on internal TCP/IP stuffs.
        '''        
        dst = self.dst
        return IP(dst=dst)
    
    def get_base_pkt(self):
        '''
        Creates a base packet based on a rcvd packet.
        '''
        return IP(dst=self.dst) / TCP(dport=self.dport, sport=self.sport)

        
    def update_seg_state(self, seg, payload=None):
        '''
        Update the state of a segment based on the TCP state.

        :param seg: segment to update the ack and seq numbers for 
        :type seg:  scapy.TCP
        '''
        seg = self.RCV.update_seg(seg)[0]
        seg, pay = self.SND.update_seg(seg, payload)
        return seg, pay

    def get_flag_val(self, flag_str):
        '''
        Get flag values based on flag string.

        :param flag_str: flag string to convert to int
        :type flag_str: string  

        :return: integer representation of the flag string
        :rtype: integer
        '''
        flags = 0
        for i in flag_str:
            flags += self.flag_vals[i]
        return flags
    
    def check_pkt(self, pkt):
        '''
        Check to see if the pkt contains a TCP segment.

        :param pkt: packet that may or may not contain a pkt
        :type pkt: scapy.Packet

        :return: TCP payload is in the packet
        :rtype: boolean
        '''
        return not pkt is None and TCP in pkt
            
    def update_from_pkt(self, pkt):
        '''
        Update TCP state from the given packet.

        :param pkt: packet that is used to update TCP state
        :type pkt: scapy.Packet

        :return: successful update            
        :rtype: boolean
        '''
        if self.check_pkt(pkt):
            seg = pkt[TCP]
            x = self.update_snd(seg)
            y = self.update_rcv(seg)
            return x and y
        return False
        
    def update_snd(self, seg):
        '''
        Update the SND (seq numbers and such) portion of the TCP SM.

        :param seg: TCP segment
        :type seg: scapy.TCP

        :return: successful update                        
        :rtype: boolean
        '''
        return self.SND.update_from_seg(seg)
    
    def update_rcv(self, seg):
        '''
        Update the RCV (rcv numbers and such) portion of the TCP SM.

        :param seg: TCP segment
        :type seg: scapy.TCP

        :return: successful update                        
        :rtype: boolean
        '''
        return self.RCV.update_from_seg(seg)
    
    # handle send syn stuff
    def create_seg(self, seg=None, flags="S", payload=None ):
        '''
        Create a segment based on the TCP SM, flags, and payload.

        :param seg: TCP segment
        :type seg: scapy.TCP
        :param flags: flags string to set in the segment
        :type flags: string
        :param payload: payload to include in the segment
        :type payload: string

        :return: tuple of the TCP segment and unused payload                        
        :rtype: (scapy.TCP, string)
        '''
        s = self.get_pkt(seg)
        seg = None
        pay = payload
        payload = None
        s, pay = self.update_seg_state(s, pay)
        s.flags = self.get_flag_val(flags)
        return s, pay
    
    def rcv_syn(self, rpkt):
        '''
        Update TCP SM based on rcv'd syn packet.

        :param rpkt: IP/TCP pkt
        :type rpkt: scapy.Packet
        '''
        self.dport = seg.sport
        self.sport = seg.dport
        self.dst = seg.src

        # init tcp state
        self.RCV.init_from_seg(rpkt[TCP])
        self.state = "SYN_RCVD"

    def rcv_syn_ans(self, rpkt, s=None):
        '''
        Update TCP SM based on rcv'd a syn packet and 
        respond automatically.

        :param rpkt: IP/TCP pkt
        :type rpkt: scapy.Packet
        :param s: socket to send packet out on
        :type s: scapy.L3Socket
        '''
        self.get_socket(s)
        s = None

        self.rcv_syn(rpkt)
        # get IP and TCP vals
        pkt = self.get_base_pkt()
        self.state = "SYN_RCVD"
        self.move_state = self.state_synrcvd
        return self.send_pkt(pkt, self.sock, flags="SA")    
        
    def rcv_synack(self, rpkt):
        '''
        Update TCP SM based on rcv'd a syn-ack packet. 

        :param rpkt: IP/TCP pkt
        :type rpkt: scapy.Packet
        '''
        if self.check_pkt(rpkt):
            self.init_from_pkt(rpkt[TCP])
    
    def rcv_synack_ans(self, rpkt, s=None):
        '''
        Update TCP SM based on rcv'd a syn-ack packet and 
        respond automatically.

        :param rpkt: IP/TCP pkt
        :type rpkt: scapy.Packet
        :param s: socket to send packet out on
        :type s: scapy.L3Socket
        '''
        self.get_socket(s)
        s = None

        self.rcv_synack(rpkt)
        pkt = self.get_base_pkt()
        print "Inside syn-ack ans machine"
        #rpkt.show()
        #pkt.show()
        return self.send_pkt(pkt, s, flags="A")
    
    def send_pkt(self, pkt=None, s=None, flags=None, payload=None):
        '''
        Update TCP Segment and Send the full packet. 

        :param s: socket to send packet out on
        :type s: scapy.L3Socket
        :param pkt: IP/TCP pkt
        :type pkt: scapy.Packet
        :param flags: flags to set in the segment
        :type flags: string
        :param payload: payload to include in the packet
        :type payload: string

        :return: packet received from sending the pkt                        
        :rtype: scapy.Packet
        '''
        p = self.get_pkt(pkt)
        self.get_socket(s)
        s = pkt = None
                    
        #pkt = self.add_ether(pkt)
        p[TCP],pay = self.create_seg(p[TCP], flags=flags, payload=payload)
        rpkt = self.send_rcv_pkts(self.sock, p)
        if rpkt is None or not TCP in rpkt:
            return None, pay
        return rpkt, pay
    
    def rcv_fin(self, pkt):
        self.update_from_pkt(pkt)
            
    def rcv_fin_ans(self, rpkt, s=None):
        # skip over FIN_WAIT_* phases and
        # LAST_ACK states
        if rpkt is None or\
            not TCP in None:
            return None
        self.rcv_fin(rpkt)
        if rpkt[TCP].flags == self.get_flag_val("F") or\
            rpkt[TCP].flags == self.get_flag_val("FA") and\
            self.state == "ESTABLISED":
            self.state = "CLOSED"
            return self.send_pkt( s=s, flags="FA")
        elif rpkt[TCP].flags == self.get_flag_val("F") or\
            rpkt[TCP].flags == self.get_flag_val("FA") and\
            self.state == "FIN_WAIT_1":
            self.state = "CLOSED"
            return self.send_pkt( s=s, flags="A")
        return (None, None)
    
    def rcv_seg_ans(self, rpkt, s):
        if rpkt is None or\
            not TCP in rpkt:
            return None
        rflags = rpkt[TCP].flags
        if rflags == self.get_flag_val("S"):
            return self.rcv_syn_ans(rpkt, s)
        elif rflags == self.get_flag_val("A"):
            # TODO this is only an ACK and 
            # ot could mean a number of things
            # this can not be answered automatically
            # yet
            return self.rcv_ack_ans(rpkt, s)
        elif rflags == self.get_flag_val("F") or\
            rflags == self.get_flag_val("FA"):
            return self.rcv_fin_ans(rpkt, s) 
        elif rflags == self.get_flag_val("SA"):
            return self.rcv_synack_ans(rpkt, s)
        elif rflags == self.get_flag_val("PA"):
            return self.rcv_pshack_ans(rpkt, s)
        
    def rcv_pshack_ans(self, rpkt, s=None):
        if rpkt is None or\
            not TCP in None:
            return None
        
        self.update_from_pkt(rpkt)
        
    def rcv_ack(self, rpkt):
        '''
        Update TCP SM based on rcv'd a ack packet.

        :param rpkt: IP/TCP pkt
        :type rpkt: scapy.Packet
        '''
        self.update_from_pkt(rpkt)
    
    def rcv_ack_ans(self, rpkt, s=None):
        self.rcv_ack(rpkt)
        return None
    
    def send_rcv_pkts(self, s, pkt):
        '''
        Send and recv packets.

        :param s: socket to send packet out on
        :type s: scapy.L3Socket
        :param pkt: IP/TCP pkt
        :type pkt: scapy.Packet

        :return: packet recieved from sending the pkt                        
        :rtype: scapy.Packet
        '''
        result = self.quick_send(s, pkt)
        if len(result[0]) == 0:
            self.seg_record.append((pkt, None))
            return None
        rpkt = result[0][0][1]
        self.seg_record.append((pkt, rpkt))
        return rpkt
    
    # TCP state transitioning takes place here
    def state_closed(self, rpkt):
        self.state == "CLOSED"
        return   self.state
    
    def state_listen(self, rpkt, s=None):
        if TCP in rpkt and\
            rpkt[TCP].flags == self.get_flag_val("S"):
            self.state = "SYN_RCVD"
            self.move_state = self.state_syn_rcvd
            self.rcv_syn(rpkt)
            return self.state
        return self.state
    
    def state_syn_rcvd(self, rpkt, s=None):
        if TCP in rpkt and\
            rpkt[TCP].flags == self.get_flag_val("A"):
            self.state = "ESTABLISHED"
            self.move_state = self.state_established(rpkt, s)
            self.rcv_ack(rpkt, s)
            #self.send_synack(pkt, s)            

    def state_syn_sent(self, rpkt, s=None):
        if TCP in rpkt and\
            rpkt[TCP].flags == self.get_flag_val("A"):
            self.state = "ESTABLISHED"
            self.move_state = self.state_established
            return self.rcv_synack_ans(rpkt, s)
    
    def state_established(self, rpkt, s=None):
        if not TCP in rpkt:
            return None
        
        if rpkt[TCP].flags == self.get_flag_val("A"):
            return self.rcv_ack(rpkt)
        elif rpkt[TCP].flags == self.get_flag_val("PA"):
            return self.rcv_pshack(seg)
        elif rpkt[TCP].flags == self.get_flag_val("RA"):
            pass
            #return self.rcv_ack(seg)
        elif rpkt[TCP].flags == self.get_flag_val("F"):
            # TODO implement rcv_fin 
            self.state = "CLOSE_WAIT"
            self.move_state = self.state_close_wait
            # do not care about the return value for the 
            # ack of the fin, since the socket will close
            # on the remote end
            rpkt2, pay= self.send_pkt(self.get_base_pkt(), s=s, flags="A")
            return self.move_state(rpkt)
            #return self.rcv_fin_ans(seg)
        elif rpkt[TCP].flags == self.get_flag_val("FA"):
            return self.rcv_finack(seg)
    
    def state_close_wait(self, rpkt, s=None):
        if self.state == "CLOSE_WAIT":
            self.state = "LAST_ACK"
            self.move_state = self.state_last_ack
            rpkt, pay = self.send_pkt(rpkt, s, flags="F")
            return self.move_state(rpkt, s)
    
    def state_last_ack(self, rpkt, s=None):
        if self.state == "LAST_ACK" and\
            TCP in rpkt and\
            rpkt[TCP].flags == self.get_flag_val("A"):
            self.state = "CLOSED"
            self.move_state = self.state_closed 
        return False
    
    def state_closing(self, rpkt, s=None):  
        if self.state == "CLOSING" and\
            TCP in rpkt and\
            rpkt[TCP].flags == self.get_flag_val("A"):
            self.state == "TIME_WAIT"
            self.move_state = self.state_time_wait
            return True
        return False
        
    def state_time_wait(self, rpkt, s=None):
        if self.state == "TIME_WAIT":
            # dont care about cheking rpkt from for an ack
            # from the fin in the closing state
            self.state = "CLOSED"
            self.move_state = self.state_closed
            return True
        return False
    
    def state_fin_wait_1(self, rpkt, s=None):
        if self.state != "FIN_WAIT_1":
            return False
        if TCP in rpkt and\
            rpkt[TCP].flage == self.get_flag_val("F"):
            self.state = "FIN_WAIT_2"
            self.move_state = self.state_fin_wait_2
            return self.move_state(rpkt)
        
        if TCP in rpkt and\
            rpkt[TCP].flags == self.get_flag_val("F"):
            # TODO implement rcv_fin_ans
            #rpkt = self.rcv_fin(rpkt, s)
            self.move_state = self.state_closing
            self.state = "CLOSING"
            return self.move_state(rpkt, s)

    def state_fin_wait_1(self, rpkt, s=None):
        if self.state == "FIN_WAIT_1" and\
            TCP in rpkt and\
            rpkt[TCP].flage == self.get_flag_val("A"):
            self.state = "TIME_WAIT"
            self.move_state = self.state_fin_wait_2
            return self.move_state(rpkt)
        
    def rcv_seg(self, rpkt):
        self.move_state(rpkt)
        
    def establish_connection(self):
        '''
        Send and recv packets.

        :param pkt: IP/TCP pkt
        :type pkt: scapy.Packet
        :param s: socket to send packet out on
        :type s: scapy.L3Socket

        :return: successful connection established,
                 packet received from sending the pkt
        :rtype: boolean, scapy.Packet
        '''
        pkt = IP(dst=self.socket.d_addr) / \
            TCP(dport=self.socket.d_port, sport=self.socket.s_port)
        
        self.socket.send(pkt)
        
        # if rpkt is None or\
        #     not self.check_flags(rpkt[TCP], "SA"):
        #     return False, rpkt 
        self.state = "SYN_SENT"
        rpkt = self.rcv_synack_ans(rpkt, s)
        return True, rpkt
    
    def listen(self):
        rpkt = self.listen_for_syn()
        rpkt = self.rcv_syn_ans(rpkt)
        if not rpkt is None:
            return True, rpkt
        return False, rpkt
    
    def simple_send_data(self, seg, payload=None):
        """
        Send data, payload, to the remote host using the TCP state machine.
        The data is contained in payload, and any payload that can not be sent
        is returned back to the user.
        
        :param seg: seg contains the data payload
        :type seg: scapy.TCP
        :param payload: seg data to send
        :type payload: string
        
        :return: successfully sent all data, unsent data
        :rtype: (boolean, string)
        """
        p = ""
        success = False
        if not payload is None:
            p = payload
            payload = None
        elif payload is None and\
            not seg.payload is None:
            p = str(seg.payload)
            seg.payload = None
        
        while 1:
            seg, p = self.SND.update_seg(seg, p)
            if seg is None:
                success = False
                break
        
        return success, p
    
    def flush_rcv_socket(self, sock):
        '''
        Flush out all the packets from a socket.

        :param sock: socket to read all data out of
        :type sock: scapy.SuperSocket

        :return: list of all the packets read out of the socket
        :rtype: list 
        '''
        
        pkts = []
        while 1:
            pkt = sock.recv(MTU)
            if pkt is None: break
            pkts.append(pkt)
        return pkts
            
    
    def listen_for_syn(self, lport, s=None, timeout=None, sel_timeout=.1):
        """
        Listen for a Syn Packet (based on sniff).

        :param lport: port to look for in the syn packet
        :type lport:  port to listen for
        :param s: scapy socket to listen on, if none one is initialized
        :type s:  scapy.L3Socket
        :param timeout: stop sniffing after a given time (default: None)
        :type timeout: int
        :param sel_timeout: select timeout period
        :type sel_timeout: int
        """
        self.get_socket(s)
        s = None
            
        syn_filter = lambda pkt: not pkt is None and\
                                 TCP in pkt and\
                                 pkt[TCP].flags == self.get_flag_val("S") and\
                                 pkt[TCP].dport == lport
        
        if timeout is not None:
            stoptime = time.time()+timeout
        remain = None
        pkts = []
        p = self.flush_rcv_socket(self.sock)
        while 1:
            try:
                if timeout is not None:
                    remain = stoptime-time.time()
                    if remain <= 0:
                        break
                sel = select([self.sock],[],[], .1)
                if not sel[0] is None:
                    p = self.sock.recv(MTU)
                    if p is None:
                        continue
                    if syn_filter(p):
                        return p
            except KeyboardInterrupt:
                break
        return None
    
    # def quick_send(self, sock, pkt, timeout=4, inter=0, verbose=None, chainCC=0, retry=0, multi=0):
    #     '''
    #     Quick send is just a wrapper around scapy sndrcv(...)
    #     Check the code or docs for keywords and other stuff, but we
    #     simply pass in a packet and a socket.
    #     
    #     :param sock: initialized socket for sending packet data
    #     :type sock: scapy.L3socket
    #     :param pkt: packet to send
    #     :type pkt: scapy.Packet 
    #     '''
    #     return sndrcv(sock, pkt, timeout, inter, verbose, chainCC, retry, multi)        
    
    # def init_socket(self, iface=None, filter=None, nofilter=0):
    #     print "Initializing Socket"
    #     return self.init_L3socket(filter=filter, nofilter=nofilter, iface=iface)
    # 
    # def init_L3socket(self, iface=None, filter=None, nofilter=0):
    #     print "Initializing Socket"
    #     self.sock = conf.L3socket(filter=filter, nofilter=nofilter, iface=iface)
    #     print "The following socket was initialized", str(socket)
    #     return self.sock
    # 
    # def init_L2socket(self, iface=None, filter=None, nofilter=0):
    #     print "Initializing Socket"
    #     self.sock = conf.L2socket(filter=filter, nofilter=nofilter, iface=iface)
    #     print "The following socket was initialized", str(socket)
    #     return self.sock

# 
# class ReadTCPCapture(TCPState):
#     def __init__(self, pcap_file_name, filter_ports=[]):
#         fports = set(filter_ports)
#         pcap = scapy.rdpcap(pcap_file_name)
#         self.pkts = [pkt for pkt in pcap if TCP in pkt and\
#                      pkt[TCP].sports not in fports and\
#                      pkt[TCP].dport not in fports]
#         self.streams = None
#         self.sessions = {}
#         self.states = {}
#     
#     def filter_tcp(self, pkts, src=None, dst=None, sport=None, dport=None, seq=None):
#         results = []
#         check = lambda arg,comp: not arg is None and comp != arg 
#         for pkt in self.pkts:
#             if check(src, pkt.src):
#                 continue
#             if check(dst, pkt.dst):
#                 continue
#             if check(sport, pkt.sport) and check(sport, pkt.dport):
#                 continue
#             if check(dport, pkt.dport) and check(dport, pkt.sport):
#                 continue
#             results.append(pkt)
#         return results
#         
#     def read_tcp_stream(self, src=None, dst=None, sport=None, dport=None, seq=None):
#         pkts = self.filter_tcp(src, dst, sport, dport)
#     
#     def find_est_conn(self, pkts, pos):
#         s_pos = pos
#         get_filter_vals = lambda pkt:pkt.src, pkt.dst, pkt.sport, pkt.dport
#         while s_pos < len(pkts):
#             # get current packet and check to see if it is a SYN
#             c_pkt = pkts[s_pos]
#             if c_pkt[TCP].flags != self.get_flag_val("S"):
#                 s_pos+=1
#                 continue
#             # grab all the remaining pkts/segments that match the c_pkt criterion
#             stream_pkts = self.filter_tcp(pkts[s_pos:], get_filter_vals(c_pkt))
#             if len(stream_pkts) > 3 and\
#                 stream_pkts[1][TCP].flags == self.get_flag_val("A") and\
#                 stream_pkts[2][TCP].flags == self.get_flag_val("SA"):
#                 end_pos = self.find_finack(stream_pkts)
#                 return stream_pkts[:end_pos], s_pos
#             s_pos+=1
#         return [],s_pos
#     
#     def find_finack(self, pkts):
#         pos = 0
#         while pos < len(pkts):
#             pkt = pkts[pos]
#             if pkt[TCP].flags == self.get_flag_val("FA"):
#                 break
#             pos+=1
#         return pos
#         
#     def get_next_stream(self, pkts, pos):
#         est_pos = find_establish_conn(pkts, pos)
#     
#     def slice_tcp_streams(self, pkts=None):
#         pkt_s = pkts
#         pkts = None
#         if pkt_s is None:
#             pkt_s = self.pkts
#         self.streams = []
#         while pos <  len(pkt_s):
#             pos, stream = self.get_next_stream(pkts, pos)
#             self.streams.append(stream)
# 
# 
#         