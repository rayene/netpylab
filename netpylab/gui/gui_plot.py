import wx.lib.plot

class Plot(wx.lib.plot.PlotCanvas):
    def __init__(self, parent):
        wx.lib.plot.PlotCanvas.__init__(self, parent)#pos, size, style, name) 

    def refresh(self, monitors):
        plots = []
        for m in monitors:
            if len(m)<2:
                continue
            plots.append(wx.lib.plot.PolyLine(m, colour=m.color, width=1))
            
        gc = wx.lib.plot.PlotGraphics(plots,
                'Title',
                't',
                'Y')
        
        # self.Draw(gc, xAxis=(0,12), yAxis=(0,30))
        self.Draw(gc)