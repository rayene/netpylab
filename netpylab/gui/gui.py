#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
#TODO: Documentation
#TODO: Emulation again
#TODO: More GPX traces
#TODO: GPS Routing
#TODO: Add TCP
#TODO: imitate socket API
#TODO: Add a state machine class
#TODO: Add a state machine creation
#TODO: Open Wireshark
#TODO: Add Unit Tests
#TODO: http://www.freesoftwaremagazine.com/columns/keeping_score_test_driven_development_python_pylint_unittest_doctest_and_pyrate
#wx.SearchCtrl
#save gui view
#TODO Add copyright
#private variables start with a _underscore
#fix shaking and label deviation
#realistic wireless network model
#sequence diagram accept nodes-only
#sequence diagram legend



# third-party modules
import wx,  wx.aui
# netpylab modules
from gui_map import MapCanvas
from gui_sequence import SequenceCanvas
from gui_log import LogListPanel
from gui_pyshell import PyShell
from gui_tree import Tree
from gui_packets import PacketTree
from gui_plot import Plot
import config
import utils

from netpylab import World
import places, nodes, interfaces, applications

class MainWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent = None, id = 1, title= 'NetPyLab')
        self.iconsize = 24
        self.Maximize()
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CLOSE, self.OnExit)
        
        self._mgr = wx.aui.AuiManager(self)
        self.menubar = self.create_menubar()

        self.tree = Tree(self)
        self.add_pane(self.tree, 'left', 'Object Tree')
        
        self.packet_tree = PacketTree(self)
        self.add_pane(self.packet_tree, 'bottom', 'Packet Tree')
        
        # self.pyfilling = wx.py.filling.Filling(self, -1,)
        # self.add_pane(self.pyfilling, 'bottom', 'Context')
        
        self.log = LogListPanel(self)
        self.add_pane(self.log, 'left', 'Log')
        
        

        self.map = MapCanvas(self)
        self.add_pane(self.map, 'center', 'Map')
        self.add_label = self.map.add_label
        
        # self.sequence = SequenceCanvas(self)
        # self.add_pane(self.sequence, 'right', 'Sequence Diagram')
        
        self.plot = Plot(self)
        self.add_pane(self.plot, 'bottom', 'Plot')

        self.pyshell = PyShell(self, -1, introText='Welcome to NetPyLab' ,style =wx.NO_BORDER)
        self.pyshell.setBuiltinKeywords()
        self.add_pane(self.pyshell, 'bottom', 'Shell')
        self.run('from netpylab import World')
        self.run('from paths import *')
        self.run('from places import *')
        self.run('from nodes import *')
        self.run('from interfaces import *')
        self.run('from applications import *')
        World.gui = self
        self.run('world = World()')
        
        self.toolbars = {}
        self.create_main_toolbar()
        self.create_other_toolbars()
                          

        
        self._mgr.Update()
        
        self.CreateStatusBar()
        
        
        
        self.target_obj = None
        self.items = []
        
        
        tbmenu = wx.Menu()
        self.viewmenu.AppendSeparator()
        self.viewmenu.AppendMenu(-1, 'Toolbars', tbmenu)
        
        for label, tb in self.toolbars.iteritems():
            n = wx.NewId()
            tbmenu.Append(n, label, label)
        
        self.mode = 'build'
    
    def OnPlot(self, e):
        # self.plot.refresh(self.world.monitors)
        pass
        
    def create_main_toolbar(self):
        t = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                         wx.TB_NODIVIDER | wx.TB_HORZ_TEXT)
        t.SetToolBitmapSize(wx.Size(self.iconsize,self.iconsize))
        bf = config.BUTTONS_FOLDER

        self.tb_button(t, self.filemenu, os.path.join(bf, 'favorite.png'), "favorite", None)
        self.tb_button(t, self.filemenu, os.path.join(bf, 'open.png'), "open", self.OnOpen, id = wx.ID_OPEN)
        self.tb_button(t, self.filemenu, os.path.join(bf, 'save.png'), "save", None)
        t.AddSeparator()
        self.tb_button(t, self.simulationmenu, os.path.join(bf, 'reload.png'), "reload", self.OnPlot)
        self.tb_button(t, self.simulationmenu, os.path.join(bf, 'play.png'), "play", self.OnPlay)
        self.tb_button(t, self.simulationmenu, os.path.join(bf, 'pause.png'), "pause", None)
        self.tb_button(t, self.simulationmenu, os.path.join(bf, 'stop.png'), "stop", None)
        self.tb_button(t, self.simulationmenu, os.path.join(bf, 'step.png'), "step", None)
        self.tb_button(t, self.simulationmenu, os.path.join(bf, 'simulate.png'), "simulate", None)
        t.AddSeparator()
        self.tb_button(t, self.viewmenu, os.path.join(bf, 'zoomin.png'), "zoom in", self.OnZoomIn)
        self.tb_button(t, self.viewmenu, os.path.join(bf, 'zoomout.png'), "zoom out", self.OnZoomOut)
        self.tb_button(t, self.viewmenu, os.path.join(bf, 'fullscreen.png'), "fullscreen", None)
        t.AddSeparator()
        self.tb_button(t, self.simulationmenu, os.path.join(bf, 'report.png'), "report", self.OnReport)
        t.AddSeparator()
        self.tb_button(t, self.viewmenu, os.path.join(bf, 'help.png'), "help", None)
        t.Realize()

        self._mgr.AddPane(t, wx.aui.AuiPaneInfo().
                          ToolbarPane().Top().
                          LeftDockable(False).RightDockable(False))        
        self.toolbars = {'Main':t}
                
    
    def OnReport(self, event):
        self.create_sequence_diagram(self.actors)
            
        
        
    def create_menubar(self):
        self.menuBar = wx.MenuBar()

        self.filemenu= wx.Menu()

        self.filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)
        self.filemenu.AppendSeparator()
        self.filemenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
        wx.EVT_MENU(self, wx.ID_ABOUT, self.OnAbout)
        self.menuBar.Append(self.filemenu,"&File")
        
        self.editmenu= wx.Menu()
        self.menuBar.Append(self.editmenu,"&Edit")
        
        self.addmenu=wx.Menu()
        self.menuBar.Append(self.addmenu,"&Add")
        
        self.simulationmenu=wx.Menu()
        self.menuBar.Append(self.simulationmenu,"&Simulation")
        
        self.viewmenu= wx.Menu()
        self.menuBar.Append(self.viewmenu,"&View")
        
        self.SetMenuBar(self.menuBar)  # Adding the MenuBar to the Frame content.
        
    def add_pane(self, control, position, label = ''):

        info = wx.aui.AuiPaneInfo().Name(label).Layer(1).CloseButton(True).MaximizeButton(True).MinimizeButton(True).MinSize(wx.Size(200,100))
        if position == 'center':
            info = info.Center()
        elif position == 'left':
            info = info.Left()
        elif position == 'right':
            info = info.Right()
        elif position == 'top':
            info = info.Top()
        elif position == 'bottom':
            info = info.Bottom()
        
        if label <> '':
            info = info.Caption(label)

        self._mgr.AddPane(control, info)

    def create_other_toolbars(self):
        self.commands = {}
        for module, ancestor_class in [(applications, applications.Application),
                            (interfaces, interfaces.Interface), 
                            (nodes, nodes.Node),
                            (places, places.Place), 
                            ]:
            t = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                         wx.TB_NODIVIDER | wx.TB_HORZ_TEXT)
            t.SetToolBitmapSize(wx.Size(self.iconsize,self.iconsize))

            self.toolbars[module.__name__] = t
            nid = wx.NewId()
            m = wx.Menu()
            self.addmenu.AppendMenu(nid, module.__name__, m)
            for cls_name, cls_type in module.__dict__.iteritems():
                try:
                    if issubclass(cls_type, ancestor_class) and cls_type <> ancestor_class:
                        imgfile = utils.default_class_img(cls_type)
                        self.tb_button(t, m, imgfile, cls_name, self.OnAddObj, cls_name)
                except TypeError:
                    pass
            t.Realize()
            self._mgr.AddPane(t, wx.aui.AuiPaneInfo().
                          ToolbarPane().Top().Layer(1).Hide().
                          LeftDockable(False).RightDockable(False))
            
    
    def icon(self, imgfile):
        return wx.Image(imgfile).Resize((400,400),(-56,-56)).Rescale(self.iconsize, self.iconsize, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        
    def tb_button(self, toolbar, menu, imgfile, label, func, class_name = None, id = None):
        if not id:
            id = wx.NewId()
        if class_name:
            self.commands[id] = class_name
        img = self.icon(imgfile)
        button = toolbar.AddLabelTool(id, label, img)
        button.class_name = class_name
        self.Bind(wx.EVT_TOOL, func, id=id)
        item = menu.Append(id, label)
        item.SetBitmap(img)

    def OnAddObj(self, event):
        cmd = self.commands[event.GetId()]+'('
        self.pyshell.write(cmd)
        self.pyshell.autoCallTipShow(cmd)
        self.pyshell.setFocus()

    def OnWorldStart(self):
        if self.mode == 'build':
            self.pyshell.pause()
            return False
        elif self.mode == 'simulate':
            return True
        else:
            assert False
        
    def OnWorldStop(self):
        # self.pyshell.pause()
        # self.mode = 'pause'
        try:
            self.plot.refresh(self.world.monitors)
        except:
            pass
        self.packet_tree.refresh()

    def OnPlay(self, event):
        if self.mode == 'build':
            self.mode = 'simulate'
            self.run('world.start()')
            self.mode = 'result'
            # self.pyshell.pause()
            self.pyshell.play()
        elif self.mode == 'simulate':
            pass
        elif self.mode == 'result':
            self.pyshell.play()
        
        
            
    def OnKeyDown(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.OnExit(None)
        elif keycode == wx.WXK_UP:
            self.map.move_camera(0,3)
        elif keycode == wx.WXK_DOWN:
            self.map.move_camera(0,3)
        elif keycode == wx.WXK_RIGHT:
            self.map.move_camera(0,3)
        elif keycode == wx.WXK_LEFT:
            self.map.move_camera(0,3)
        elif keycode == wx.WXK_SPACE:
            self.OnZoomIn()
        elif keycode == wx.WXK_SHIFT:
            self.OnZoomOut()
        else:
            event.Skip()
    
    def run(self, command):
        self.pyshell.run(command)
        
    def OnZoomIn(self, event=None):
        self.map.zoom +=1

    def OnZoomOut(self, event=None):
        self.map.zoom -=1

    def OnNewWorld(self, world):
        # self.world = world
        world.log.addHandler(self.log.handler)
        self.tree.create_world()
        

    def add_item(self, item):
        self.items.append(item)
        self.map.add_item(item)
        self.tree.add_item(item)

    @property
    def world(self):
        return World.current_world
    
    def create_sequence_diagram(self, actors):
        self.actors = actors
        self.sequence = SequenceCanvas(self, actors)
        self.add_pane(self.sequence, 'right', 'Sequence Diagram')
        self._mgr.Update()

    def OnAbout(self,e):
        # First we create and fill the info object
        from wx.lib.wordwrap import wordwrap
        licenseText = "blah " * 250 + "\n\n" +"yadda " * 100
        info = wx.AboutDialogInfo()
        info.Name = "Hello World"
        info.Version = "1.2.3"
        info.Copyright = "(C) 2006 Programmers and Coders Everywhere"
        info.Description = wordwrap(
            "A \"hello world\" program is a software program that prints out "
            "\"Hello world!\" on a display device. It is used in many introductory "
            "tutorials for teaching a programming language."
            
            "\n\nSuch a program is typically one of the simplest programs possible "
            "in a computer language. A \"hello world\" program can be a useful "
            "sanity test to make sure that a language's compiler, development "
            "environment, and run-time environment are correctly installed.",
            350, wx.ClientDC(self))
        info.WebSite = ("http://en.wikipedia.org/wiki/Hello_world", "Hello World home page")
        info.Developers = ["Main developer: Rayene Ben Rayana"]

        info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)
    
    def OnExit(self,e):
        self.map.world_map.stop()
        if self.world:
            self.world.stop()
        self.Destroy() # Close the frame.
    
    def OnOpen(self,e):
        """ Open a file"""
        self.dirname = '../demo_scripts'
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.filename=dlg.GetFilename()
            self.dirname=dlg.GetDirectory()
            f=os.path.join(self.dirname,self.filename)
            dlg.Destroy()
        else:
            dlg.Destroy()
            return
        self.pyshell.runfile(f)
        self.pyshell.play()

    def refresh(self):
        wx.SafeYield(self, True)
        # self.map.OnDraw()


class NetPyLabGui(wx.App):
    def OnInit(self):
        bmp = wx.Image(config.LOGO).Rescale(400,300, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        wx.SplashScreen(bmp, wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_TIMEOUT,
                2000, None, -1, size = (300,600))
        wx.Yield()
        main_window = MainWindow()
        main_window.Show()
        return True

def main():
    app = NetPyLabGui()
    app.MainLoop()