import wx

import os
import config
import utils

class Tree(wx.TreeCtrl):
    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent, -1, wx.Point(0, 0), wx.Size(200, 250),
            style = wx.TR_DEFAULT_STYLE | wx.NO_BORDER)
        self.parent = parent
        self.items = {}
        self.root = None
        self.images = wx.ImageList(self.parent.iconsize, self.parent.iconsize)
        self.SetImageList(self.images)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
    
    def OnSelChanged(self, event):
        item = event.GetItem()
        for k, i in self.items.iteritems():
            if i == item:
                self.parent.target_obj = k
        
    def create_world(self):
        if self.root:
            return
        imgfile = os.path.join(config.SPRITES_FOLDER, 'globe.png')
        
        img = self.parent.icon(imgfile)
        self.a = self.images.Add(img)
        self.root = self.AddRoot("World", self.a)
        self.Expand(self.root)
    
    def add_item(self, item):
        if hasattr(item, 'node'):
            n = self.items[item.node]
        elif hasattr(item, 'place'):
            n = self.items[item.place]
        elif self.root:
            n=self.root
        else:
            return
        try:
            imgfile = utils.default_class_img(item.__class__)
            img = self.parent.icon(imgfile)
            i = self.images.Add(img)
            self.items[item] = self.AppendItem(n, item.label, i)
        except:
            self.items[item] = self.AppendItem(n, item.label)
            