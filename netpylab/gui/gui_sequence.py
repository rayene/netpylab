import wx, wx.glcanvas
import pyglet
import gui_shapes
import packets

from gui_camera import Camera

class SequenceCanvas(wx.glcanvas.GLCanvas, packets.SequenceDiagram):
    def __init__(self, parent, actors):
        wx.glcanvas.GLCanvas.__init__(self, parent,-1)
        self.line_batch = pyglet.graphics.Batch()
        self.text_batch = pyglet.graphics.Batch()
        self.parent = parent
        wx.EVT_PAINT(self, self.OnPaint)
        self.Bind(wx.EVT_TIMER, self.OnPaint)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftMouseButtonDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftMouseButtonUp)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseScroll)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.selected_sprite = None
        self.is_dragging =False
        self.is_fullscreen_set = False
        self.__zoom = 3
        self.target_zoom = 8
        color_white = (1, 1, 1, 1)
        pyglet.gl.glClearColor(*color_white)
        pyglet.gl.glEnable(pyglet.gl.GL_LINE_SMOOTH)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        self.Bind(wx.EVT_KEY_DOWN, self.parent.OnKeyDown)
        self.camera = Camera((0, 0), pow(2, 18-self.__zoom))
        packets.SequenceDiagram.__init__(self, parent.world.packets, actors, xzoom = 200, yzoom = -200, spritezoom = 3)
        self.SetCurrent()
        self.timer.Start(100)

    def OnMouseScroll(self, event):
        delta = event.m_wheelRotation
        self.zoom+= max(min(delta,2),-2)

    def OnMotion(self, event):
        x,y = event.GetPositionTuple()
        if event.Dragging():
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
            if self.parent.target_obj:
                self.parent.target_obj = None
            self.move_camera(self.mouse_x-x,
                            -(self.mouse_y-y))
        self.mouse_x, self.mouse_y = x,y
    
    def move_camera(self, x, y):
        self.camera.target.x += self.camera.scale*x/100
        self.camera.target.y += self.camera.scale*y/100
        
            
    def OnLeftMouseButtonDown(self, event):
        pass
        
    def OnLeftMouseButtonUp(self, event):
        self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    @property
    def world(self):
        return self.parent.world
        
    def OnPaint(self,event):
        self.SetCurrent()
        pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT| pyglet.gl.GL_DEPTH_BUFFER_BIT)
        if self.world:
            self.width, self.height = self.GetSize().width, self.GetSize().height
            if self.target_zoom <> self.__zoom:
                self.camera.zoom(pow(2, self.__zoom - self.target_zoom))
                self.__zoom = self.target_zoom
            # Updating the camera
            self.camera.update()
            self.camera.focus(self.width, self.height)
            self.line_batch.draw()
            # self.camera.focus3(self.width, self.height)
            self.text_batch.draw()
            # self.camera.hud_mode(self.width, self.height)
        self.SwapBuffers()
    
    @property
    def zoom(self):
        return self.__zoom
    
    @zoom.setter
    def zoom(self, new_zoom):
        self.target_zoom = min( max(new_zoom,-20), 40)
    
    def zoom_in(self):
        self.zoom +=1
    
    def zoom_out(self):
        self.zoom -=1

    def draw_text(self, x, y, label, font_size):
        l = gui_shapes.Text(self.text_batch, label, font_size = font_size, delta_y = 0, anchor_y = 'bottom')
        l.update(x, y)

    def draw_line(self, x1, y1, x2, y2, color, width):
        l = gui_shapes.Line(self.line_batch, color1 = [0,0,0,1])
        l.update(x1, y1, x2, y2)

    def draw_sprite(self, x, y, sprite, color, size):
        l = gui_shapes.Polygon(self.line_batch, sides = 12, size = size, color1 = color)
        l.update(x, y)