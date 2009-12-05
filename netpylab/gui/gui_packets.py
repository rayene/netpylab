import  wx
import wx.html

#----------------------------------------------------------------------------

class PacketTree(wx.TreeCtrl):
    

# class PacketTree(wx.Treebook):
    def __init__(self, parent, id = -1):
        wx.TreeCtrl.__init__(self, parent, id)
        self.parent = parent
        # self.win = wx.Panel(self, -1)
        
        # self.html = MyHtmlWindow(self.win)
        # self.box = wx.BoxSizer(wx.VERTICAL)
        #         self.box.Add(self.html, 1, wx.GROW)
        # self.win.SetSizer(self.box)
        # self.win.SetAutoLayout(True)

        
        # self.text = wx.TextCtrl(self.win, -1)

    def refresh(self):
        self.root = self.AddRoot("Packets")
        for p in self.parent.world.packets:
            p_node = self.AppendItem(self.root, "(%d) %s" % (p.number, p.description))
            self.parent.refresh()
            for ts in p.trip:
                ts_node = self.AppendItem(p_node, str(ts))
                self.AppendItem(ts_node, "Summary: " +ts.data.summary())
                self.AppendItem(ts_node, "Scapy command: "+ ts.data.command())
                lays_node = self.AppendItem(ts_node, "Layers")
                pl, layers = ts.data.build_ps()
                while layers:
                    layer, fields = layers.pop()
                    layer_node = self.AppendItem(lays_node, layer.name)
                    for fieldname, fieldval, fielddump in fields:
                        self.AppendItem(layer_node, "%s : %s" %(fieldname.name , fieldval))
                        
                    

        self.Expand(self.root)
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.Bind(wx.EVT_TREEBOOK_PAGE_CHANGING, self.OnPageChanging)

        # This is a workaround for a sizing bug on Mac...
        # wx.FutureCall(100, self.AdjustSize)

    # def AdjustSize(self):
    #     #print self.GetTreeCtrl().GetBestSize()
    #     self.GetTreeCtrl().InvalidateBestSize()
    #     self.SendSizeEvent()
    #     #print self.GetTreeCtrl().GetBestSize()
        

    # def makeColorPanel(self, color):
    #     p = wx.Panel(self, -1)
    #     win = ColoredPanel(p, color)
    #     p.win = win
    #     def OnCPSize(evt, win=win):
    #         win.SetPosition((0,0))
    #         win.SetSize(evt.GetSize())
    #     p.Bind(wx.EVT_SIZE, OnCPSize)
    #     return p


    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        self.html.SetPage('<html><body>%s</body></html>' % self.pos[new].html())
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

class MyHtmlWindow(wx.html.HtmlWindow):
    def __init__(self, parent):
        wx.html.HtmlWindow.__init__(self, parent, -1, style=wx.NO_FULL_REPAINT_ON_RESIZE)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()

    def OnLinkClicked(self, linkinfo):
        super(MyHtmlWindow, self).OnLinkClicked(linkinfo)

    def OnSetTitle(self, title):
        super(MyHtmlWindow, self).OnSetTitle(title)

    def OnCellMouseHover(self, cell, x, y):
        super(MyHtmlWindow, self).OnCellMouseHover(cell, x, y)

    def OnCellClicked(self, cell, x, y, evt):
        if isinstance(cell, wx.html.HtmlWordCell):
            sel = wx.html.HtmlSelection()
        super(MyHtmlWindow, self).OnCellClicked(cell, x, y, evt)
