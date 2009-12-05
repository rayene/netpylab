from math import cos, sin, pi
import pyglet

import Image as Im
class Shape(object):
    def  __init__(self, batch):
        self.batch = batch


class Image(Shape):
    def  __init__(self, batch, img_path):
        Shape.__init__(self, batch)
        self.zoom = 160
        img = self.load_img(img_path)
        self.pyglet_sprite = pyglet.sprite.Sprite(img, x=0  , y=0, blend_src=770, blend_dest=771, usage='dynamic', batch = self.batch)
        
    def load_img(self, img_path):
        # img = pyglet.image.load(img_path)
        img = Im.open(img_path)
        img = img.resize((self.zoom, self.zoom), Im.NEAREST)
        img.save("/tmp/temp.png")
        img = pyglet.image.load("/tmp/temp.png")

        img.anchor_x = img.width/2
        img.anchor_y = img.height/2
        return img
    
    @property
    def visible(self):
        return self.pyglet_sprite.visible
        
    @visible.setter
    def visible(self, is_visible):
        self.pyglet_sprite.visible = is_visible

    def width(self):
        return self.pyglet_sprite.width

    def height(self):
        return self.pyglet_sprite.height

    def set_opacity(self, opacity):
        self.pyglet_sprite.opacity = opacity 

            
    def update(self, x, y):
        self.pyglet_sprite.x = x
        self.pyglet_sprite.y = y


class Text(Shape):
    def  __init__(self, batch, text, font_size = 22, delta_y = -50, anchor_y = 'top'):
        Shape.__init__(self, batch)
        self.delta_y = delta_y
        if len(text)>10:
            text = text[:7]+'...'
        self._text = text
        self.label = pyglet.text.Label(text, font_name = 'Arial', 
                    font_size = font_size,
                    bold = True, italic = False, color = (0, 0, 0, 170),
                    x = 0, y = 0, 
                    width = None, height = None,
                    anchor_x = 'center', anchor_y = anchor_y,
                    halign = 'center', multiline = False, 
                    dpi = None, batch = batch)
    
    @property
    def visible(self):
        return self.label.text <> ''
        
    @visible.setter
    def visible(self, is_visible):
        if is_visible:
            self.label.text = self._text
        else:
            self.label.text = ''
            
        
    def width(self):
        return self.label.width
    def height(self):
        return self.label.height
    def set_text(self, text):
        self.label.text = text
    def delete(self):
        self.label.delete()
        
    def update(self, x, y):
        self.label.x = x#+self.delta_x
        self.label.y = y+self.delta_y

class Polygon(Shape):
    def __init__(self, batch = None, sides= 30, size = 5, color1 = [0,0,0,1], color2 = None,  filled = True, contour = True):
        assert sides >= 3
        Shape.__init__(self, batch)
        self.sides = sides
        self.size = size
        self.color1 = color1
        self.color2 = color2 if color2 else color1
        self.filled = filled
        self.contour = contour
        self.pi_n = (2*pi)/self.sides
        self.points = (self.sides+1) * [0,0]
        
        if self.filled:
            self.indices = (self.sides)*[0,0,0]
            for i in xrange(self.sides):
                self.points[2*i+2] = self.size*cos(i*self.pi_n)
                self.points[2*i+3] = self.size*sin(i*self.pi_n)
                self.indices[3*i+1] = i+1
                self.indices[3*i+2] = i+2
            self.indices[-1] = 1
            
            self.vt = batch.add_indexed(self.sides+1, pyglet.gl.GL_TRIANGLES, 
                    None, self.indices, 
                    ('v2f', self.points), 
                    ('c4f', self.color1+ self.sides*(self.color2)))

        if self.contour:
            self.indices = (self.sides)*[0,0]
            for i in xrange(self.sides):
                self.indices[2*i] = i+1
                self.indices[2*i+1] = i+2
            self.indices[-1] = 1
            
            self.vl = batch.add_indexed(self.sides+1, pyglet.gl.GL_LINES, None,
                                    self.indices,
                                    ('v2f', self.points),
                                    ('c4f', self.color1*(self.sides+1)))
        self.p = (self.sides+1) * [0,0]

    def update(self, x, y):
        for i in xrange(self.sides+1):
            self.p[2*i] = x + self.points[2*i]
            self.p[2*i+1] = y + self.points[2*i+1]
        
        if self.filled:
            self.vt.vertices = self.p

        if self.contour:
            self.vl.vertices = self.p

class Line(Shape):
    def  __init__(self, batch, color1 = [0,0,0,1], color2 = None):
        Shape.__init__(self, batch)
        color2 = color2 if color2 else color1

        self.line = batch.add(2, pyglet.gl.GL_LINES, None,
                            ('v2f', (0, 0, 0, 0)),
                            ('c4f', color1+color2))        

    def update(self, x1, y1, x2, y2):
        self.line.vertices = (x1, y1, x2, y2)

    def delete(self):
        self.line.delete()
                
class Link(Line):
    """Line Help"""
    def  __init__(self, batch,  target, color1 = [0,0,0,1], color2 = None):
        Line.__init__(self, batch, color1, color2)
        self.target = target
        
    def update(self, x, y):
        self.line.vertices = (x, y, self.target.x, self.target.y)



            
        