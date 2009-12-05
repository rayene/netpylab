from netpylab import NetpylabProcess
from paths import PointPath

class Place(NetpylabProcess):
    def __init__(self, world, path, label=''):
        self.path = path
        NetpylabProcess.__init__(self, world, label = label)
        self.nodes=[]
        self.active = False
        
        self.reachable_access_points = []
        self.world.places.append(self)
        
    # def scan_access_points(self):
    #     reachable = []
    #     for name, obj in self.world.objects.iteritems():
    #         if WirelessAccessPoint in obj.__class__.__mro__:
    #             if self.distance(obj) <obj.Range():
    #                 reachable.append(obj)
    #                 #print "Reachable : ", obj.label, self.distance(obj)
    #     self.reachable_access_points = reachable
    #     for node in self.nodes:
    #         for interface in node.interfaces():
    #             if WirelessInterface in interface.__class__.__mro__:
    #                 interface.access_points_updated(reachable)
    
    def run(self):
        i = 0
        while True:
            try:
                dt = self.path[i+1].time - self.path[i].time
            except:
                break
            yield self.hold, self, dt
    # def distance(self, obj):
    #     ox, oy = obj.position
    #     return math.sqrt((self.x - ox)**2 + (self.y - oy)**2)

    def reachable_access_points(self):
        return self.reachable_access_points

    def attach_node(self,node):
        self.nodes.append(node)
#        self.world.log(self.label, "added_node " + node.label)

    @property
    def position(self):
        return self.path.position(self.world.time)
    
    @property
    def speed(self):
        return self.path.position(self.world.time).speed

    def info(self):
        return '%s speed: %.1f Km/h' %(self.label, self.speed)

class Human(Place): # :)
    pass

class Car(Place):
    pass

class Train(Place):
    pass

class Building(Place):
    def __init__(self, world, lat = 48.110282, lon = -1.609004, label=''):
        Place.__init__(self, world, PointPath(lat, lon), label = label)

class Anchor(Building):
    # """An anchor is an invisible building (graphically speaking)
    # 
    # """
    pass


