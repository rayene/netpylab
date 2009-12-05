#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This is the core of the NetPyLab Network Emulator"""
__author__ = "Rayene Ben Rayana"
__date__ = "26 July 2008"
__version__ = "$Revision: 1.0 $"
__credits__ = ["JMB, G, C"]
__copyright__ = "Copyright 2009,"
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Rayene Ben Rayana"
__email__ = "rayene.benrayana@gmail.com"
__status__ = "unstable"
__docformat__ = 'restructuredtext'

import logging
import channels
#-----------------------------------------------------------------------
from packets import PacketList
from SimPy.SimulationStep import SimulationStep as Sim, Process, SimEvent, hold, waitevent

class Column(list):
    def __init__(self, func, label, color):
        list.__init__(self)
        self.func = func
        self.color = color
        if not label:
            label = func.__name__
        self.label = label

class Monitor(object):
    def __init__(self, world, time_label = 'time(s)'):
        """A monitor is an grid"""
        self.world = world
        self.columns = []
        self.watch(lambda: self.world.time,  time_label)

    def watch(self, func, label = None, color = 'red'):
        self.columns.append(Column(func, label, color))
        if self.world.gui:
            self.world.gui.add_label(lambda: label + ' : ' + str(func()))
            
    def observe(self):
        for c in self.columns:
            c.append(c.func())

    def plot(self):
        pass


# class Plot(SimPyPlot):
#     pass

class NetpylabSimulation(Sim):
    pass

class NetpylabObject(object):
    """docstring for NetpylabObject"""
    label_index=0
    def __init__(self, world , label=''):
        if label:
            self.label = label
        else:
            self.label = self.auto_label()

        self.world = world
        self.world.add(self)
        self.world.log.info(self.label + ' has been created')
        self.active=True
        self.history = []
    

    def auto_label(self):
        NetpylabObject.label_index+=1
        return self.__class__.__name__+str(NetpylabObject.label_index)

    def __str__(self):
        return self.label

    def stop(self, at=0):
        pass

    def add_to_history(self, event, description = ''):
        self.history.append([self.world.time, event, description])

class NetpylabProcess(NetpylabObject, Process):
    def __init__(self, world, label=''):
        NetpylabObject.__init__(self, world, label)
        Process.__init__(self, sim=self.world)
        self.hold = hold
        self.waitevent = waitevent

    def start(self, at=0):
        if at:
            self.world.activate(self, self.run(), at=at)
        else:
            self.world.activate(self, self.run())
    
class NetpylabThread(Process):
    def __init__(self, creator):
        self.creator = creator
        self.world = creator.world
        self.hold = hold
        self.waitevent = waitevent
        Process.__init__(self, sim=self.world)

    
    def start(self):
        self.world.activate(self, self.run())

class CallLater(NetpylabThread):
    def __init__(self, creator, delay, action, args=None, autostart = True):
        NetpylabThread.__init__(self, creator)
        self.action = action
        self.delay = delay
        self.args = args
        if autostart:
            self.start()

    def run(self):
        yield hold, self, self.delay
        self.cmd()
        
    def cmd(self):
        if self.args:
            self.action(self.args)
        else: 
            self.action()
                    
class Loop(CallLater):

    def run(self):
        while True:
            self.cmd()
            yield hold, self, self.delay

class NetpylabEvent(SimEvent):
    pass

class World(NetpylabSimulation):
    current_world = None
    gui = None
    
    def __init__(self):
        """Create a world object
        
        The world is the main object of the topology. It gathers all the 
        other objects such as places, nodes, etc.
        
        The world handles also the simulation/emulation routines. You can set:
        world.until = 300 
        to limit the simulation/emulation time to 300 seconds.
        
        Later, you can call :
        world.start()
        to start the simulation.

        It is a NetPyLab convention to create a world using the command :
        world = World()
        """
        self.real_time = False
        self.speed_scale=1
        self.loglevel=4
        self.until = 300
        NetpylabSimulation.__init__(self)
        
        self.monitor = Monitor(self)
        self.create_logger(self.loglevel)
        
        channels.init_wireless_channels(self)
        self.objects={}
        self.places = []
        self.packets = PacketList()
        self.interfaces = []
        self.nodes = []
        self.start_time = -1

        self.channels = {}
        World.current_world = self
        self.initialize() # initialize simulation
        if self.gui:
            self.gui.OnNewWorld(self)
        self.log.info("World Created")        
    @property
    def time(self):
        return self.now()

    def create_logger(self, loglevel):
        log_levels=[logging.CRITICAL, 
                    logging.ERROR, 
                    logging.WARNING, 
                    logging.INFO, 
                    logging.DEBUG]
        self.log = logging.getLogger("NetpylabLogger")
        self.log.setLevel(log_levels[loglevel])
        #create console handler and set level to debug
        if not self.gui:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(levelname)0.10s\tin %(module)20.20s\tline%(lineno)5.5s\t %(message)s")
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
        
    def add(self, obj):
        if self.objects.has_key(obj.label):
            raise RuntimeError(obj.label + " Already registred ! choose another label")
        self.objects[obj.label]= obj
        if self.gui:
            self.gui.add_item(obj)

    def list(self):
        for obj_name, obj in self.objects.iteritems():
            print obj_name + "\t\t\t" + obj.__class__.__name__
            
    def find(self, class_name_list):
        objs = []
        for obj_name, obj in self.objects.iteritems():
            if obj.__class__.__name__ in class_name_list:
                objs.append(obj_name)
        return objs

    def register_channel(self, channel):
        try:
            self.channels[channel.__class__].append(channel)
        except:
            self.channels[channel.__class__] = [channel]
        
    def sequence_diagram(self, actors, xzoom = 200, yzoom = -200, spritezoom = 3):
        if self.gui:
            self.gui.create_sequence_diagram(actors)
        
    def obj(self,name):
        try:
            return self.objects[name]
        except:
            raise name + " does not exist !"
    
    def start(self):
        
        if self.gui:
            if not self.gui.OnWorldStart():
                return  
        try:
            self.startStepping()
            # real_time = self.real_time,
            # rel_speed=self.speed_scale
            self.simulate(until = self.until, callback = self.call_gui)
        except KeyboardInterrupt:
            pass
        
        if self.gui:
            self.gui.OnWorldStop()
                
    # import time
    def call_gui(self):
        self.monitor.observe()
        if self.gui:
            self.gui.refresh()
            # time.sleep(0.5)

        
    def stop(self):
        self.stopSimulation()

def load_script(script):
    _locals = locals()
    _globals = globals()
    execfile(script,  _globals, _locals)


def usage():
    print """   Usage:
        -h, --help     : Display this message
        -d             : Debug mode
        -t             : Command line (text) mode
        -s <my_script.py> : Execute my_script.py"""

import sys, getopt
    
def main(argv):
    script = None
    text = False
    try: 
        opts, args = getopt.getopt(argv, "hdts:", ["help", "debug", "text", "script="])
    except getopt.GetoptError:          
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == '-d':
            global _debug
            _debug = 1
            print 'Debug Mode'
        elif opt in ('-t', '--text'):
            text = True
            return
        elif opt in ("-s", "--script"):
            script = arg
    if not script:
        script = 'scripts/MobileIPv6_Ethernet.py'

    if text:
        load_script(script)
    else:
        import gui.gui
        global win
        gui.gui.main()
        
if __name__ == '__main__':
    main(sys.argv[1:])
