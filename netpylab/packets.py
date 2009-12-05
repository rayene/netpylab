import sys

# from scapy.utils import colgen
import colors

#from netpylab import NetpylabThread#, NetpylabEvent

class Packet(object):
    number = 1
    def __init__(self, creator, data, description, filter_tag):

        self.__dict__['initialized'] = False
        self.data = data
        self.misc = {}
        self.number = Packet.number
        Packet.number += 1
        self.world = creator.world
        self.trip = []
        self.add_to_trip(creator, 'created')
        self.description = description
        self.filter_tag = filter_tag
        self.world.packets.append(self)
        self.initialized = True

    def add_to_trip(self, actor, action, info = ''):
        self.trip.append(TripStop(self.world.time, self, actor, action, info, self.data.copy()))

    def summary(self):
        return self.data.summary()

    def command(self):
        return self.data.command()

    def history(self):
        return ''.join(str(ts) for ts in self.trip)

    def __repr__(self):
        return '(%d) %s\n%s\n%s\n%s' % (self.number, 
                                        self.description, 
                                        self.summary(), 
                                        self.command(), 
                                        self.history())
    
    def html(self):
        content = """
<h1>(%d) %s</h1><br/>
<h2>%s</h2><br/>
<h3>%s</h3><br/><hr/>""" % (self.number, 
                            self.description, 
                            self.summary(), 
                            self.command())
        for ts in self.trip:
            content += ts.html()
        return content

    def __str__(self):
        return self.__repr__()
    
    # @property  
    # def data(self):
    #     raise

    def __getitem__(self, cls):
        return self.data[cls]

    def __setitem__(self, cls, val):
        self.data[cls] = val

    def __contains__(self, cls):
        return self.data.haslayer(cls)
    
    def __delitem__(self, cls):
        del(self.data[cls])

    def add_on_top(self, layer):
        self.data = self.data / layer

    def add_at_bottom(self, layer):
        self.data = layer/ self.data
    
    def remove_from_top(self, how_many = 1):
        self.data = self.data[0:-1-how_many]
            
    def remove_from_bottom(self, how_many = 1):
        for i in range(0, how_many):
            self.data = self.data.payload

    def __getattr__(self, attr_name):
        try:
            return self.__dict__[attr_name]
        except:
            return self.data.__getattr__(attr_name)
    @property
    def payload(self):
        return self.data.payload
        
    def __setattr__(self, attr_name, attr_val):
        if (self.initialized and attr_name in self.__dict__) or not self.initialized:
            self.__dict__[attr_name] = attr_val
        else:
            self.data.__setattr__(attr_name, attr_val)

    def build_ps(self):
        return self.data.build_ps()
    
class TripStop(object):
    def __init__(self, time, packet, actor, action, info, data):
        self.time = time
        self.packet = packet
        self.actor = actor
        self.action = action
        self.info = info
        self.data = data
        try:
            self.hierarchy = str(self.actor.node) + '.'
        except:
            self.hierarchy = ''

    def __str__(self):
        return (' :: %s by %s%s at %f %s\n' % 
            (self.action, self.hierarchy, str(self.actor), self.time, self.info))

    def __repr__(self):
        return self.__str__()

    def html(self):
        dump = '<table width="100%"><tr>'
        shift = 0
        larg = 16
        backcolor=colgen(0.6, 0.8, 1.0)
        forecolor=colgen(0.2, 0.5, 0.8)
        content =  ('<h4>%s by %s%s at %f</h4> %s<br>' % 
            (self.action, self.hierarchy, str(self.actor), self.time, self.info))
        pl, layers = self.data.build_ps()
        
        def htmlcol(col):
            return '#%02x%02x%02x' % (col[0]*255, col[1]*255, col[2]*255)
            
        while layers:
            layer, fields = layers.pop()
            bkcol = htmlcol(backcolor.next())
            content += '<table width="100%%" bgcolor=%s><tr><td><h6>%s</h6></td></tr>' % (bkcol, layer.name)
            for fieldname, fieldval, fielddump in fields:
                frcol = htmlcol(forecolor.next())
                if fieldval is not None:
                    if len(fieldval) > 24:
                        fieldval = fieldval[:21]+"..."
                else:
                    fieldval=""
                content += '<tr><td>%s : %s</td></tr>' %(fieldname.name, fieldval)
                while fielddump:
                    dmp, fielddump = fielddump[:larg-shift],fielddump[larg-shift:]
                    for c in dmp:
                        dump += '<td bgcolor=%s><font face="courier new">%02x</font></td>' % (bkcol, ord(c))
                    shift += len(dmp)
                    if shift >= larg:
                        shift = 0
                        dump += '</tr><tr>'
            content += '</table>'
        dump += '</tr></table>'
        return '<table border="10"><tr><td>%s</td><td>%s</td></tr></table>'%(content, dump)
        print content
        # return content + dump
        

class PacketList(list):
    def __init__(self):
        list.__init__(self)

    def text(self):
        s = ''
        for p in self:
            s += str(p) +'\n'
        return s

    def filter(self, action, actor):
        result = PacketList()
        for p in self:
            for trip_stop in p.trip:
                if trip_stop.action == action and trip_stop.actor == actor:
                    result.append(p)
        return result
    
    @property
    def diagram(self):
        return SequenceDiagram(self)

class Action(object):
    def __init__(self, sprite = None, size = 3, color = colors.black, travel=True, travel_desc=False):
        self.sprite = sprite
        self.size = size
        self.color = color
        self.travel = travel
        self.travel_desc = travel_desc

actions_sprites = {
    'created':Action('circle', 5, colors.white, False),
    'sent':Action(),
    'broadcasted':Action(),
    'received':Action(travel_desc=True),
    'retired':Action('circle', 3, colors.greenyellow),
    'refused':Action('circle', 4, colors.red),
    'routed':Action(),
    'bridged':Action(),
    'enqueued':Action('circle', 3, colors.orange),
    'dequeued':Action('circle', 3, colors.orange),
    'deleted':Action('circle', 3, colors.red),
    'not routed':Action('circle', 4, colors.red),
    'accepted':Action(),
    'tunneled':Action('circle', 4, colors.dodgerblue),
    'detunneled':Action('circle', 4, colors.dodgerblue),
    'not tunneled':Action('circle', 3, colors.darkmagenta),
    'L2_dispatched':Action(),
    'L3_dispatched':Action(),
    'L4_dispatched':Action(),
    'not L2_dispatched':Action('circle', 4, colors.maroon),
    'not L3_dispatched':Action('circle', 4, colors.maroon),
    'not L4_dispatched':Action('circle', 4, colors.maroon),
    'unreachable':Action('circle', 4, colors.purple),
    }

class SequenceDiagram(object):
    def __init__(self, packet_list, actors, xzoom = 100000, yzoom = -200, spritezoom = 3):
        self.actors = actors
        self.xzoom = xzoom
        self.yzoom = yzoom
        self.spritezoom = spritezoom
        self.max_time = 0
        self.min_time = sys.maxint
        self.max_x = 0
        self.verticals = {}
        self.max_x = 0
        
        for actor in actors:
            if type(actor) == tuple:
                for a in actor:
                    self.verticals[a] = self.max_x
                    self.max_x+=self.xzoom*0.3
            else:
                self.verticals[actor] = self.max_x
            self.max_x+=self.xzoom
                
        for p in packet_list:
            old_ts = None
            for ts in p.trip:
                if ts.actor not in self.verticals:
                    continue

                action = actions_sprites[ts.action]

                self.max_time = max(ts.time, self.max_time)
                self.min_time = min(ts.time, self.min_time)

                if action.travel:
                    if old_ts:
                        x1 = self.verticals[old_ts.actor]
                        y1 = old_ts.time * self.yzoom
                        x2 = self.verticals[ts.actor]
                        y2 = ts.time * self.yzoom
                        self.draw_line(x1, y1, x2, y2,
                                        color = [0,0,0,1],
                                        width = 1)
                        # self.draw_text(int((3*x1+x2)/4),int((3*y1+y2)/4), 
                        #     label = '12',
                        #     font_size = 12)
                        
                        # self.draw_text(int((x1+x2)/2),int((y1+y2)/2), 
                        #     label = '(%d) %s' % (p.number, p.description), 
                        #     font_size = 28)

                if action.sprite:
                    self.draw_sprite(   x = self.verticals[ts.actor], 
                                        y = ts.time * self.yzoom,
                                        sprite = action.sprite, 
                                        color = list(action.color)+[1],
                                        size = action.size * self.spritezoom)
                old_ts = ts
                                        
                                    
        for actor, x in self.verticals.iteritems():
            self.draw_line( x1 = x, 
                            y1 = self.min_time*self.yzoom,
                            x2 = x, 
                            y2 = self.max_time*self.yzoom,
                            color = [0,0,0,1],
                            width = 2)
            
            self.draw_text( x = x,
                            y = self.min_time*self.yzoom,
                            label = actor.label,
                            font_size = 18)

        self.height = (self.max_time - self.min_time) * self.zoom
        self.width = self.max_x
        

    def draw_text(self, x, y, label, font_size):
        pass
    def draw_line(self, x1, y1, x2, y2, color, width):
        pass
    def draw_sprite(self, x, y, sprite, color, size):
        pass