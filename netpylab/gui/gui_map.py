import math
import pyglet
import os
import urllib, threading
import Queue

import wx, wx.glcanvas
import gui_sprites
from paths import Point
import config

how_many_threads = 4

from gui_camera import Camera

pow2 = [2**i for i in range(30)] # avoids to caculate 2**n too often
pow2_25 = 2**25
pow2_26 = 2*pow2_25

class MapCanvas(wx.glcanvas.GLCanvas):
    def __init__(self, parent):
        wx.glcanvas.GLCanvas.__init__(self, parent,-1)
        self.parent = parent
        wx.EVT_PAINT(self, self.OnPaint)
        self.Bind(wx.EVT_TIMER, self.OnPaint)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftMouseButtonDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftMouseButtonUp)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseScroll)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        # self.Bind(wx.EVT_SIZE, self.OnResize)

        self.init = 0
        self.selected_sprite = None
        self.is_dragging =False
        self.is_fullscreen_set = False
        self.__zoom = 1
        self.target_zoom = 3
        self.labels = []
        # color_gray = 0.95, 0.93, 0.91, 1
        color_gray = 1, 1, 1, 1
        pyglet.gl.glClearColor(*color_gray)
        pyglet.gl.glEnable(pyglet.gl.GL_LINE_SMOOTH)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        
        self.Bind(wx.EVT_KEY_DOWN, self.parent.OnKeyDown)
        self.scene = gui_sprites.Scene(self)
    
        #win.add_label(lambda: str(win.world_map.batch_down.remaining()), 340, 18)
        self.add_label(lambda: 'zoom: '+ str(self.zoom))

    # def OnResize(self, event):
    #     pass
    
    def add_item(self, item):
        class_name = item.__class__.__name__+'Sprite'
        sprite_class = gui_sprites.__dict__[class_name]
        item.sprite = sprite_class(self.scene, item)
        
        
    def OnMouseScroll(self, event):
        delta = event.m_wheelRotation
        self.zoom += max(min(delta,2),-2)

    def add_label(self, lambda_text):
        self.labels.append(gui_sprites.Label(self.scene, lambda_text))

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
        if not self.init:
            self.InitGL()
            self.init = 1
            self.timer.Start(50)
        self.SetCurrent()
        self.OnDraw()
        return
    
    def InitGL(self):        
        
        # self.group = pyglet.graphics.OrderedGroup(20)
        self.world_map = WorldMap(self, 128, 1)
        self.camera = Camera((0, 0), pow(2, 7+18-self.__zoom))
    

    def OnDraw(self):
        pyglet.gl.glClear(pyglet.gl.GL_COLOR_BUFFER_BIT ) #| pyglet.gl.GL_DEPTH_BUFFER_BIT
                
        # Looking for objects to draw
        if self.world:
            self.width, self.height = self.GetSize().width, self.GetSize().height
            if self.target_zoom <> self.__zoom:
                self.camera.zoom(pow(2, self.__zoom - self.target_zoom))
                self.world_map.zoom = self.target_zoom
                self.__zoom = self.target_zoom
        
            # Updating the camera
            self.camera.update()
            self.camera.focus(self.width, self.height)
            if self.parent.target_obj:
                try:
                    point = self.parent.target_obj.position
                    self.world_map.geo_focus(point)
                    self.geo_target(point)
                except AttributeError:
                    pass
            else:
                self.map_target(self.camera.target.x, self.camera.target.y)

            # 
            for obj in self.parent.items:
                obj.sprite.update()

            # Draw the world Map
            self.world_map.draw()
            

            # Draw the paths and the ranges
            self.scene.draw_ranges()

            # Change the projection matrix of the camera to draw places, nodes, ...
            self.camera.focus2(self.width, self.height)
        
            # draw places, nodes, ifaces, apps, etc.
            self.scene.draw_icons()
        
            # Change the projection matrix again
            self.camera.hud_mode(self.width, self.height)
            
            for l in self.labels:
                    l.update()
                    
            self.scene.draw_labels()
        self.SwapBuffers()
    
    @property
    def zoom(self):
        return self.__zoom
    
    @zoom.setter
    def zoom(self, new_zoom):
        self.target_zoom = min( max(new_zoom,0), 20)
    
    def zoom_in(self):
        self.zoom +=1
    
    def zoom_out(self):
        self.zoom -=1
    
    def geo_target(self, point):
        self.world_map.geo_focus(point)
        self.camera.target.x = point.x
        self.camera.target.y = point.y
    
    def map_target(self, xm, ym):
        xo, yo = self.world_map.map2osm(xm, ym)
        self.world_map.map_focus((xo, yo))
        self.camera.target.x = xm
        self.camera.target.y = ym
    
    def scr2map(self, xs, ys):
        ratio = float(self.width)/self.height
        xm = ((float(xs) / self.width)-0.5)*self.camera.scale*2.0*ratio + self.camera.x
        ym = ((float(ys) /self.height)-0.5)*self.camera.scale*2.0 + self.camera.y
        return xm, ym
    
    def map2scr(self, xm, ym):
        ratio = float(self.width)/self.height
        xs = (((float(xm)-self.camera.x)/(self.camera.scale*2.0*ratio))+0.5)*self.width
        ys = (((float(ym)-self.camera.y)/(self.camera.scale*2.0))+0.5)*self.height
        return xs, ys
    
    def map2scr2(self, xm, ym):
        diff = self.camera.desc_layer_scale/self.camera.scale
        return (xm)*diff, (ym)*diff


class WorldMap(object):
    
    """ The are 18 levels of zoom. When zoom == 0, a single png picture
        represents the whole world (world) 256x256. when zoom == 1, 4 pictures
        of the same size replace the first one. For zoom == 18, 2**18 pictures
        replace the first picture.
        
        The more the zoom level, the more the images are and the more they are
        scaled down to fit in the same size as the first image. 
        
        Zoom == 0,  1 image,        scaled to 2**(18- 0):
        Zoom == 1,  4 images,       scaled to 2**(18- 1):
        Zoom == 2, 16 images,       scaled to 2**(18- 2):
            :
            :
        Zoom == n, 2**(2*n) images, scaled to 2**(18- n):
            :
            :
        Zoom == 18, 2**(2*18) images, scaled to 1:
        """

    def __init__(self, win, opacity, max_download, target = None):
        self.win = win
        self.map={}
        self._zoom = 0
        self.opacity = opacity
        self.focus = Point(0.0,0.0)
        self.batch_pool=[]
        self.which_thread = 0
        for i in range(19):
            self.batch_pool.append(pyglet.graphics.Batch())

        self.thread_pool = []
        for i in range(how_many_threads):
            f = FileGetter(self)
            self.thread_pool.append(f)

        # self.geo_focus(Point(48.120205,-1.639238), True)
        if not os.path.exists(config.MAP_CACHE_FOLDER):
            os.mkdir(config.MAP_CACHE_FOLDER)
    
    @property
    def batch(self):
        return self.batch_pool[self.zoom]
    
    def draw(self):

        self.batch.draw()

    #@property
    def get_zoom(self):
        return self._zoom
            
    #@zoom.setter            
    def set_zoom(self, z):
        z=min(z,18)
        z=max(z,0)
        if z != self._zoom:
            self._zoom = z
            self.n_tiles = int(pow(2,z))
            self.geo_focus(self.focus, True)
    zoom = property(get_zoom, set_zoom)
    
    def zoom_in(self):
        self.zoom+=1
    def zoom_out(self):
        self.zoom-=1

    def y2lat(self, y):    
        return (180.0/math.pi) * (2 * math.atan(math.exp(y*math.pi/180.0)) - math.pi/2.0)
        
    def lat2y(self, lat):
        return (180.0/math.pi) * math.log(math.tan(math.pi/4.0+lat*(math.pi/180.0)/2.0))

    def geo_focus(self, focus_point, zoom = None):
        if not zoom:
            zoom = self.zoom
        self.focus = focus_point
        self.map_focus((focus_point.xo, focus_point.yo), zoom)

    
    def map2osm(self, xm, ym):
        osmx, osmy = ((float(xm)/pow2_25)+1)/2, ((-float(ym)/pow2_25)+1)/2
        return osmx, osmy
    
    def meter2pixel(self, distance_in_meter):
        return pow2_26 * 1.5 * distance_in_meter / 40041455.0

    def get_lon_lat(self, scren_x,screen_y):
        """ Gives the latitude and longitude of a screen point."""
        return 1.0,1.0
    
    def stop(self):
        for f in self.thread_pool:
            f.task_queue.put('stop')

    def map_focus(self, map_focus, zoom =None):
        if not zoom:
            zoom = self.zoom
        n_tiles = int(pow(2,zoom))
        tile_xf, tile_yf = map_focus
        tile_x, tile_y = int(n_tiles*tile_xf), int(n_tiles*tile_yf)
        
        for f in self.thread_pool:
            while not f.finished_queue.empty():
                imgtask = f.finished_queue.get_nowait()
                imgtask.display()
                f.finished_queue.task_done()
        
        xl,yl = [],[]
        for i in range(0, 3):
            xl += [tile_x+i, tile_x-i]
            yl += [tile_y+i, tile_y-i] 
        for i in xl:
            if i<0 or i>=n_tiles:
                continue
            for j in yl:
                if j<0 or j>=n_tiles:
                     continue
                if not self.map.has_key((zoom, i,j)):
                    imgtask = ImgTask(zoom, i,j, self, self.batch_pool[zoom])
                    self.map[(zoom, i,j)] = imgtask
                    
                    if os.path.exists(imgtask.filepath):
                        imgtask.display()
                    else:
                        f = self.thread_pool[self.which_thread]
                        self.which_thread = (self.which_thread +1)%how_many_threads
                        f.task_queue.put(imgtask)

class ImgTask(object):
    def __init__(self, zoom, x, y, map, batch):
        self.x, self.y, self.zoom = x,y,zoom
        self.map = map
        self.batch = batch
        self.sprite = None
        self.img = None
    
    @property
    def url(self):
        return 'http://c.tile.openstreetmap.org/%d/%d/%d.png' % (self.zoom, self.x, self.y )
    
    @property    
    def filepath(self):
        return os.path.join(config.MAP_CACHE_FOLDER, '%d-%d-%d.png' % (self.zoom, self.x, self.y ))


    def display(self):
        try:
            self.img = pyglet.image.load(self.filepath)
        except:
            os.remove(self.filepath) # clean cache
            
        self.img.anchor_x = self.img.width/2
        self.img.anchor_y = self.img.height/2
        p = pow2[self.zoom]
        scale = pow2[18-self.zoom]
        self.sprite = pyglet.sprite.Sprite(self.img, 
                                    x= (self.x*2-(p-1))*128*scale, 
                                    y=-(self.y*2-(p-1))*128*scale, 
                                    blend_src=770, blend_dest=771, 
                                    batch = self.batch, 
                                    usage='static')
        self.sprite.opacity = self.map.opacity
        self.sprite.scale = scale
        
class FileGetter(threading.Thread):
    def __init__(self, world_map):
        self.world_map = world_map
        self.task_queue = Queue.LifoQueue()
        self.finished_queue = Queue.LifoQueue()
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        while True:
            imgtask = self.task_queue.get()
            if imgtask == 'stop':
                return
            try:
                urllib.urlretrieve (imgtask.url, imgtask.filepath)
            except IOError:
                print "Could not open document: %s" % imgtask.url
            self.finished_queue.put(imgtask)
            self.task_queue.task_done()

