from math import atan2, cos, sin
import pyglet

import gui_shapes
import utils
class Scene(object):
    def  __init__(self, win):
        self.win = win
        self.txt_batch = pyglet.graphics.Batch()
        self.node_batch = pyglet.graphics.Batch()
        self.iface_batch = pyglet.graphics.Batch()
        self.range_batch = pyglet.graphics.Batch()
        self.link_batch = pyglet.graphics.Batch()
        self.labels_batch = pyglet.graphics.Batch()

    def draw_ranges(self):
        pyglet.gl.glLineWidth(5)
        self.range_batch.draw()

    def draw_icons(self):
        pyglet.gl.glLineWidth(2)
        self.link_batch.draw()
        self.node_batch.draw()
        self.iface_batch.draw()
        self.txt_batch.draw()

    def draw_labels(self):
        self.labels_batch.draw()
    


class Label():
    y_start = 10
    def __init__(self, scene, func=None):
        self.func = func
        self.text = pyglet.text.Label('',
                          font_name='Arial',
                          font_size=18,
                          color=(0, 0, 0, 190),
                          x=10, y=Label.y_start,
                          batch = scene.labels_batch)
        Label.y_start += 30

    def update(self):
        if self.func:
            new_text = self.func()
            if new_text != self.text.text:
                self.text.text = new_text


##############################################################
class NoSprite(object):
    def  __init__(self, scene, obj):
        pass
    def update(self):
        pass
    
    def delta_move(self, dx, dy):
        pass


class SpriteContainer(object):
    def  __init__(self, scene):
        self.scene = scene
        self.x = self.y = 0
        self.shapes = []
        self._visible = True
        
    def add_shape(self, shape):
        self.shapes.append(shape)
        
    def update(self):
        if self.visible:
            for shape in self.shapes: shape.update(self.x, self.y)

    @property    
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self, is_visible):
        self._visible = is_visible
        for shape in self.shapes: shape.visible = is_visible
    
    def delta_move(self, dx, dy):
        self.x+=dx
        self.y+=dy

class GenericSprite(SpriteContainer):
    def __init__(self, scene, obj):
        SpriteContainer.__init__(self, scene)
        self.obj = obj

        self.selected = False

        self.txt = gui_shapes.Text(self.scene.txt_batch, 
                                    text = self.obj.label)
        self.add_shape(self.txt)
        
    def is_clicked(self, x, y):
        x2 = self.img.x
        y2 = self.img.y
        w2 = self.img.width() / 2.0
        h2 = self.img.height() / 2.0
        if x>x2-w2 and y>y2-h2 and x<x2+w2 and y<y2+h2 :
            return True
        return False

    def on_click(self):
        if not self.selected:
            self.select()
        else:
            self.unselect()

    def select(self):
        #self.background.set_opacity(255)
        self.selected = True

    def unselect(self):
        #self.background.set_opacity(0)
        self.selected = False

#----------------------------------------------------------------------
class PlaceSprite(GenericSprite):
    def __init__(self, scene, obj):
        GenericSprite.__init__(self, scene, obj)
        self.xabs = self.yabs = 0
        imgfile = utils.default_class_img(obj.__class__)
        self.img = gui_shapes.Image(self.scene.node_batch, imgfile)
        self.add_shape(self.img)
        
        #draw the location path
        glpoints = []
        l = len(self.obj.path)
        if l>1:
            for pt in self.obj.path:
                glpoints += [pt.x, pt.y]
        
            self.scene.range_batch.add(l,
                pyglet.gl.GL_LINE_STRIP, None,  
                ('v2f', glpoints), ('c4f', (0, 0, 255, 0.5)*l))

            # self.range = gui_shapes.Polygon(self.scene.range_batch, size = 200, color1 = [0,0,0,1], color2 = [0,0,0,1], filled =True, contour = True)
            # pt = self.obj.path[0]
            # self.range.update(pt.x, pt.y)

    def update(self):
        x,y = self.scene.win.map2scr2(self.obj.position.x, self.obj.position.y)
        if (self.x, self.y) != (x,y):
            dx, dy = x-self.x, y-self.y
            self.x, self.y = x,y
            GenericSprite.update(self)
            for c in self.children:
                c.sprite.delta_move(dx, dy)
                for a in c.applications + c.interfaces:
                    a.sprite.delta_move(dx, dy)

    @property
    def children(self):
        return self.obj.nodes

class AnchorSprite(PlaceSprite):
    pass
    
class BuildingSprite(PlaceSprite):
    pass

class HumanFeetSprite(PlaceSprite):
    pass

class CarSprite(PlaceSprite):
    pass

class TrainSprite(PlaceSprite):
    pass

#----------------------------------------------------------------------
class ChildSprite(GenericSprite):
    """docstring for ChildSprite"""
    def __init__(self, scene, obj):
        GenericSprite.__init__(self, scene, obj)
        self.link = gui_shapes.Link(self.scene.link_batch, self.parent)
        self.add_shape(self.link)
        self.placement = 'float'
        self.dx = 0
        self.dy = 0

    def fruchterman_reingold(self, parent, concurrent_sprites, peers = {},charges = 100000, spring_strength = 15, dist=150):
        """docstring for Fruchterman-Reingold"""
        forcex, forcey = 0,0
        
        for i, p in peers.iteritems():
            forcex += self.hooke_attraction(self.x, i.sprite.x, spring_strength)
            forcey += self.hooke_attraction(self.y, i.sprite.y, spring_strength)
        
        for other in concurrent_sprites:
            if not hasattr(other, 'x'):
                continue
            fx, fy = self.coulomb_repulsion(self.x, self.y, other.x, other.y, charges)
            forcex -= fx
            forcey -= fy
        dx, dy = self.parent_link(forcex, forcey, dist)
        a = 0.9
        self.dx = a*self.dx + (1-a)*dx +1
        self.dy = a*self.dy + (1-a)*dy
        return parent.x + self.dx, parent.y +self.dy
        
    def coulomb_repulsion(self, x1, y1, x2, y2, charges):
        dx, dy = x2-x1, y2-y1
        repulsion_norm = charges/(dx**2 + dy**2+1)
        return (dx*repulsion_norm, dy*repulsion_norm)
        
    def hooke_attraction(self, x1, x2, spring_strength):
        return spring_strength*((x2-x1))

    def parent_link(self, forcex, forcey, dist):
        alpha = atan2(forcey, forcex)
        return dist*cos(alpha), dist*sin(alpha)


    def update(self):
        if self.placement == 'static' or len(self.parent.children)== 1:
            self.x, self.y = self.parent.x, self.parent.y
            self.parent.visible = False
        elif self.placement == 'float':
            others = []
            peers = self.peers if hasattr(self, 'peers') else {}
            for obj in self.scene.win.parent.items:
                if (obj not in self.children and obj != self.obj \
                    and issubclass(obj.sprite.__class__, ChildSprite)):
                    others.append(obj.sprite)
            self.x, self.y = self.fruchterman_reingold(self.parent, others, peers)
        GenericSprite.update(self)

class NodeSprite(ChildSprite):
    def __init__(self, scene, obj):
        ChildSprite.__init__(self, scene, obj)
        imgfile = utils.default_class_img(obj.__class__)
        self.img = gui_shapes.Image(self.scene.node_batch, imgfile)
        self.add_shape(self.img)
        
    @property
    def parent(self):
        return self.obj.place.sprite

    @property
    def children(self):
        return self.obj.interfaces + self.obj.applications

    
class IPNodeSprite(NodeSprite):
    pass

class IPRouterSprite(NodeSprite):
    pass

class AccessPointSprite(NodeSprite):
    def __init__(self, scene, obj):
        NodeSprite.__init__(self, scene, obj)
        self.img.visible = False
        self.placement  = 'static'
    def connect_to(self, network_sprite):
        pass
        
class MobileNodeSprite(NodeSprite):
    pass

class MobileNodeMCoASprite(NodeSprite):
    pass
    
class CorrespondentNodeSprite(NodeSprite):
    pass

class HomeAgentSprite(NodeSprite):
    pass

class HomeAgentMCoASprite(NodeSprite):
    pass
    
class MobileRouterSprite(NodeSprite):
    pass
#----------------------------------------------------------------------
class WiredNetworkSprite(GenericSprite):
    pass
    
class TunTapNetworkSprite(WiredNetworkSprite):
    pass

class EthernetNetworkSprite(WiredNetworkSprite):
    pass

class LoopbackSprite(NoSprite):
    pass

#----------------------------------------------------------------------
class WirelessNetworkSprite(GenericSprite):
    def __init__(self, scene, obj):
        GenericSprite.__init__(self, scene, obj)
        self.ranges=[]

class WifiNetworkSprite(WirelessNetworkSprite):
    net_color="GREEN"

class UmtsNetworkSprite(WirelessNetworkSprite):
    net_color="BLUE"

class WimaxNetworkSprite(WirelessNetworkSprite):
    net_color="RED"

#----------------------------------------------------------------------
class InterfaceSprite(ChildSprite):
    
    def __init__(self, scene, obj):
        ChildSprite.__init__(self, scene, obj)
        self.txt.delta_y = 0
        self.color = list(obj.__class__.color)
        self.shape = gui_shapes.Polygon(self.scene.iface_batch, sides= 4, 
            size = 32, color1 = self.color+[0.8], filled = True, contour = False)
        self.add_shape(self.shape)
        self.children = []
        self.peers = {}
        if self.obj.node.sprite.placement == 'static':
            self.placement = 'static' 
            # self.visible = False
        
        
    @property
    def parent(self):
        return self.obj.node.sprite

    def update(self):
        for peer in self.peers.keys(): 
            if peer not in self.obj.peers:
                self.peers[peer].delete()
                del self.peers[peer]
        for peer in self.obj.peers:
            if peer not in self.peers:
                l = gui_shapes.Link(self.scene.link_batch, peer.sprite, color1 = self.color+[1], color2 = self.color+[0])
                self.add_shape(l)
                self.peers[peer] = l
        ChildSprite.update(self)

class WirelessInterfaceSprite(InterfaceSprite):
    def __init__(self, scene, obj):
        InterfaceSprite.__init__(self, scene, obj)
        size = self.scene.win.world_map.meter2pixel(self.obj.range)
        c = list(obj.color)
        self.range = gui_shapes.Polygon(self.scene.range_batch, size = size, color1 = c+[0.5], color2 = c+[0.2], filled =True, contour = True)
        self.range_x, self.range_y = 0, 0

    def update(self):
        point = self.obj.position
        if (self.range_x, self.range_y) <> (point.x, point.y):
            self.range_x, self.range_y = point.x, point.y
            self.range.update(self.range_x, self.range_y)
        InterfaceSprite.update(self)
    
class WifiInterfaceSprite(WirelessInterfaceSprite):
    pass

class WimaxInterfaceSprite(WirelessInterfaceSprite):
    pass

class UmtsInterfaceSprite():
    pass

class WiFiInterfaceSprite(WirelessInterfaceSprite):
    pass

class WiMaxInterfaceSprite(WirelessInterfaceSprite):
    pass


class MobileIPv6TunnelSprite(InterfaceSprite):
    pass

class TunTapInterfaceSprite(InterfaceSprite):
    pass

class EthernetInterfaceSprite(InterfaceSprite):
    pass

class TunTapAccessPointSprite(AccessPointSprite):
    pass
    
class EthernetSwitchSprite(AccessPointSprite):
    pass

class WirelessAccessPointSprite(AccessPointSprite):
    pass        

class WiFiAccessPointSprite(WirelessAccessPointSprite):
    pass

class WiMaxAccessPointSprite(WirelessAccessPointSprite):
    pass

class UmtsAntennaSprite(WirelessAccessPointSprite):
    pass

#----------------------------------------------------------------------

class ApplicationSprite(ChildSprite):
    def __init__(self, scene, obj):
        ChildSprite.__init__(self, scene, obj)
        self.shape = gui_shapes.Polygon(self.scene.iface_batch, sides= 12, size = 32, color1 = [1,0,0,0.8], filled = True, contour = False)
        self.txt.delta_y = 0
        self.add_shape(self.shape)
        self.children = []

    @property
    def parent(self):
        return self.obj.node.sprite

class WhiteFountainSprite(ApplicationSprite):
    pass

class BlackHoleSprite(ApplicationSprite):
    pass

class AnsweringMachineSprite(ApplicationSprite):
    pass

class ClientSprite(ApplicationSprite):
    pass
    
class ServerSprite(ApplicationSprite):
    pass

class CircularTrajectorySprite(WifiNetworkSprite):
    pass

class WirelessLinkSprite(WifiNetworkSprite):
    pass
#----------------------------------------------------------------------

# class MappedSprite(SpriteContainer):
#     def  __init__(self, scene, obj):
#         SpriteContainer.__init__(self, scene)
# 
#         self.batch = self.scene.range_batch
#         self.obj = obj
#         self.obj.sprite = self
# 
# 
# class NetRangeSprite(MappedSprite):
#     def  __init__(self, scene, obj):
#         MappedSprite.__init__(self, scene, obj)
# 
# 

class WiFiChannelSprite(NoSprite):
    pass
class WiMaxChannelSprite(NoSprite):
    pass
class EthernetCableSprite(NoSprite):
    pass

