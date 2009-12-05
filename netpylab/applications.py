""" dc """

from scapy.layers import inet, inet6
from netpylab import NetpylabProcess
from sockets import VirtSocket, IPV4, IPV6
import __socket as socket


class Application(NetpylabProcess):
    
    def __init__(self, node, label =''):
        self.node = node
        NetpylabProcess.__init__(self, node.world, label)
        node.applications.append(self)
        
        self.world = self.node.world
    
    def run(self):
        yield self.hold, self, 100
    
    def receive(self, p):
        self.world.log.warning('This should not happen. Have to be overloaded')
    
    def isIPv4(self, ipAddress):
        dots = ipAddress.split(".")
        if len(dots) != 4:
            return False
        for item in dots:
            if not 0 <= int(item) <= 255:
                return False
        return True
    
    def which_family(self, addr):
        if self.isIPv4(addr):
            return socket.AF_INET
        return socket.AF_INET6

class WhiteFountain(Application):
    def __init__(self, node, dst_ip, iface = None, label = '', dst_port=40, interval = 0.5, data_size =10):
        Application.__init__(self, node, label)
        
        self.i=0 # sent ps counter
        self.interval = interval
        self.data_size = data_size
        
        if self.isIPv4(dst_ip): family = IPV4
        else: family = IPV6
        self.s = VirtSocket(app =self,
                            receive_func = self.receive,
                            family = family,
                            proto = inet.UDP,
                            dst_ip = dst_ip,
                            dst_port = dst_port,
                            src_port = None,
                            iface=iface,
                            )
    
    def run(self):
        while True:
            if self.s.open():
                break
            else:
                self.add_to_history("unable to open socket")
                yield self.hold, self, self.interval
        while True:
            self.send()
            yield self.hold, self, self.interval
    
    def send(self):
        # self.add_to_history("sending p",  str(p.number) + p.description )
        self.s.send(str('a' * self.data_size))
        self.i+=1
    
    def receive(self, p):
        self.add_to_history("received a p",  str(p.number) + p.description)
        
        p.add_to_trip(self, 'retired')
    
    def info(self):
        return '%s sent : %3d ps' % (self.label, self.i)

class BlackHole(Application):
    def __init__(self, node, label ='', port=40):
        Application.__init__(self, node, label)
        self.received = 0
        
        #self.node.register(self, ip_family='inet', proto='UDP', port=port)
        
        self.s = VirtSocket(app =self,
                            receive_func = self.receive,
                            family = IPV6,
                            proto = inet.UDP,
                            dst_ip = None,
                            dst_port = None,
                            src_port = port
                            )
    
    def run(self):
        while True:
            if self.s.open():
                break
            else:
                self.add_to_history("unable to open socket")
                yield self.hold, self, 1
    
    def info(self):
        return '%s rcvd : %3d ps' % (self.label, self.received)
    
    def receive(self, p):
        self.received += 1
        self.add_to_history("received a p",  str(p.number) + p.description)
        p.add_to_trip(self, 'retired')


class AnsweringMachine(BlackHole):
    def receive(self, p):
        BlackHole.receive(self, p)
        # print p
        # raise
        self.s.send(str(self.received), p[inet6.IPv6].src, p.sport)

class FTPClient(WhiteFountain):
    def run(self):
        while True:
            if self.s.open():
                break
            else:
                self.add_to_history("unable to open socket")
                yield self.hold, self, 1
        self.send()


class FTPServer(BlackHole):
    def receive(self, p):
        BlackHole.receive(self, p)
        while True:
            self.s.send(str(self.received), p[inet6.IPv6].src, p.sport)


class Client(Application):
    def __init__(self, node, dst_ip, proto = 'udp', iface = None, label = '', dst_port=40, interval = 0.5, data_size =10):
        Application.__init__(self, node, label)
        self.addr = (dst_ip,dst_port)
        if proto == 'udp':
            self.proto = socket.SOCK_DGRAM
        elif proto == 'tcp':
            self.proto = socket.SOCK_STREAM
        else:
            raise RuntimeError('only TCP and udp are supported, not :' + str(proto))
        self.s = socket.socket(self, socket.AF_INET6, self.proto)

    def run(self):
        if self.proto == socket.SOCK_STREAM:
            self.s.connect(self.addr) # connect to server on the port
            while (True):
                self.s.send('Hello world')               # send the data
                yield self.hold, self, 1
        else:
            while (True):
                self.s.sendto(str('a' * self.data_size), self.addr)
                yield self.hold, self, 1
            self.s.close()

class Server(Application):
    def __init__(self, node, label ='', ip_version = 6, proto = 'udp', port=40):
        Application.__init__(self, node, label)
        self.buf = 1024
        self.addr = ('',port)
        if proto == 'udp':
            self.proto = socket.SOCK_DGRAM
        elif proto == 'tcp':
            self.proto = socket.SOCK_STREAM
        else:
            raise RuntimeError('only TCP and udp are supported, not :' + str(proto))        
        if ip_version == 6:
            family = socket.AF_INET6
        else:
            family = socket.AF_INET
        self.s = socket.socket(self, family, self.proto)#create socket
        
    
    def run(self):
        self.s.bind(self.addr) # bind the socket to the server port
        self.s.listen(5) # allow 5 simultaneous pending connections
        if self.proto == socket.SOCK_STREAM:
            while True:
                connection, address = self.s.accept()
                while True:
                    data = connection.recv(self.buf) # receive bytes
                    if data:
                        connection.send('echo -> ' + data)
                    else:
                        break
                    yield self.hold, self, 1
                yield self.hold, self, 1
                connection.close()
        else:
            while True:
                data,addr = self.s.recvfrom(self.buf)
                if not data:
                    print "Client has exited!"
                    break
                else:
                    print "\nReceived message '", data,"'"    
                yield self.hold, self, 1
            self.s.close()