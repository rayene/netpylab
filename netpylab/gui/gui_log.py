import logging
import sys
import wx
import wx.lib.mixins.listctrl  as  listmix

import config


#TODO: fix colors

class LogToList(logging.Handler):
    def __init__(self, list_ctrl):
        logging.Handler.__init__(self)
        self.list = list_ctrl.list
        self.idx1 = list_ctrl.idx1
        
        self.list.InsertColumn(0, "Level")
        self.list.InsertColumn(1, "Time", wx.LIST_FORMAT_RIGHT)
        self.list.InsertColumn(2, "Message")
        self.list.InsertColumn(3, "File")
        
        self.list.SetColumnWidth(0, 70)
        self.list.SetColumnWidth(1, 50)
        self.list.SetColumnWidth(2, 300)
        self.list.SetColumnWidth(3, 200)

        self.levels = {
                    10:('debug:',wx.CYAN),
                    20:('info:',wx.GREEN),
                    30:('warning:',wx.RED),
                    40:('error:',wx.RED),
                    50:('critical:',wx.BLACK),
                    }
        self.first = True
                    



    
    def emit(self, record):
        if self.first:
            self.first = False
            self.f_t = record.created

        lvl, color = self.levels[record.levelno]
        file_line = "%s - %s - %d" %(record.filename, record.funcName, record.lineno)
        index = self.list.InsertImageStringItem(sys.maxint, lvl, self.idx1)
        self.list.SetStringItem(index, 1, str(record.created - self.f_t))
        self.list.SetStringItem(index, 2, record.msg)
        self.list.SetStringItem(index, 3, file_line)
        # self.list.SetItemData(index, key)
        item = self.list.GetItem(1)
        item.SetTextColour(color)
        
        # self.grid.table.data.append([ 
        #     record.levelno,
        #     record.msecs,
        #     record.msg,
        #     
        #     ])
        # # self.grid.AppendRows(1)
        # self.grid.ForceRefresh()
        
# contents= ['created', 'exc_info', 'exc_text', 'filename', 'funcName', 'getMessage', 'levelname', 'levelno', 'lineno', 'module', 'msecs', 'msg', 'name', 'pathname', 'process', 'processName', 'relativeCreated', 'thread', 'threadName']

class LogList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)


class LogListPanel(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)

        tID = wx.NewId()
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        if wx.Platform == "__WXMAC__" and \
               hasattr(wx.GetApp().GetTopWindow(), "LoadDemo"):
            self.useNative = wx.CheckBox(self, -1, "Use native listctrl")
            self.useNative.SetValue( 
                not wx.SystemOptions.GetOptionInt("mac.listctrl.always_use_generic") )
            self.Bind(wx.EVT_CHECKBOX, self.OnUseNative, self.useNative)
            sizer.Add(self.useNative, 0, wx.ALL | wx.ALIGN_RIGHT, 4)
            
        self.il = wx.ImageList(16, 16)
        img = wx.Image(config.LOGO).Rescale(16,16, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        self.idx1 = self.il.Add(img)
        # self.sm_up = self.il.Add(images.SmallUpArrow.GetBitmap())
        # self.sm_dn = self.il.Add(images.SmallDnArrow.GetBitmap())

        self.list = LogList(self, tID,
                                 style=wx.LC_REPORT 
                                 #| wx.BORDER_SUNKEN
                                 | wx.BORDER_NONE
                                 | wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 #| wx.LC_NO_HEADER
                                 #| wx.LC_VRULES
                                 #| wx.LC_HRULES
                                 #| wx.LC_SINGLE_SEL
                                 )
        
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        sizer.Add(self.list, 1, wx.EXPAND)



        # Now that the list exists we can init the other base class,
        # see wx/lib/mixins/listctrl.py
        # self.itemDataMap = musicdata
        listmix.ColumnSorterMixin.__init__(self, 3)
        #self.SortListItems(0, True)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnItemDelete, self.list)
        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
        self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag, self.list)
        self.Bind(wx.EVT_LIST_COL_DRAGGING, self.OnColDragging, self.list)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColEndDrag, self.list)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.list)

        self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

        # for wxMSW
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)

        # for wxGTK
        self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
        
        self.handler = LogToList(self)


    def OnUseNative(self, event):
        wx.SystemOptions.SetOptionInt("mac.listctrl.always_use_generic", not event.IsChecked())
        wx.GetApp().GetTopWindow().LoadDemo("ListCtrl")

    # def PopulateList(self):
    #     if 0:
    #         # for normal, simple columns, you can add them like this:
    # 
    #     else:
    #         # but since we want images on the column header we have to do it the hard way:
    #         info = wx.ListItem()
    #         info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
    #         info.m_image = -1
    #         info.m_format = 0
    #         info.m_text = "Artist"
    #         self.list.InsertColumnInfo(0, info)
    # 
    #         info.m_format = wx.LIST_FORMAT_RIGHT
    #         info.m_text = "Title"
    #         self.list.InsertColumnInfo(1, info)
    # 
    #         info.m_format = 0
    #         info.m_text = "Genre"
    #         self.list.InsertColumnInfo(2, info)
    # 
    #     # items = musicdata.items()
    #     # for key, data in items:
    #     #     index = self.list.InsertImageStringItem(sys.maxint, data[0], self.idx1)
    #     #     self.list.SetStringItem(index, 1, data[1])
    #     #     self.list.SetStringItem(index, 2, data[2])
    #     #     self.list.SetItemData(index, key)
    # 
    # 
    #     # show how to select an item
    #     self.list.SetItemState(5, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
    # 
    #     # show how to change the colour of a couple items
    #     item = self.list.GetItem(1)
    #     item.SetTextColour(wx.BLUE)
    #     self.list.SetItem(item)
    #     item = self.list.GetItem(4)
    #     item.SetTextColour(wx.RED)
    #     self.list.SetItem(item)
    # 
    #     self.currentItem = 0


    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    # def GetSortImages(self):
    #     return (self.sm_dn, self.sm_up)


    def OnRightDown(self, event):
        x = event.GetX()
        y = event.GetY()
        item, flags = self.list.HitTest((x, y))

        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)

        event.Skip()


    def getColumnText(self, index, col):
        item = self.list.GetItem(index, col)
        return item.GetText()


    def OnItemSelected(self, event):
        ##print event.GetItem().GetTextColour()
        self.currentItem = event.m_itemIndex

        if self.currentItem == 10:
            #event.Veto()  # doesn't work
            # this does
            self.list.SetItemState(10, 0, wx.LIST_STATE_SELECTED)

        event.Skip()


    def OnItemDeselected(self, evt):
        item = evt.GetItem()

        # Show how to reselect something we don't want deselected
        if evt.m_itemIndex == 11:
            wx.CallAfter(self.list.SetItemState, 11, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)


    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex

    def OnBeginEdit(self, event):
        event.Allow()

    def OnItemDelete(self, event):
        pass

    def OnColClick(self, event):
        event.Skip()

    def OnColRightClick(self, event):
        item = self.list.GetColumn(event.GetColumn())


    def OnColBeginDrag(self, event):
        pass
        ## Show how to not allow a column to be resized
        #if event.GetColumn() == 0:
        #    event.Veto()


    def OnColDragging(self, event):
        pass

    def OnColEndDrag(self, event):
        pass

    def OnDoubleClick(self, event):
        event.Skip()

    def OnRightClick(self, event):

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            self.popupID6 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnPopupFour, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.OnPopupFive, id=self.popupID5)
            self.Bind(wx.EVT_MENU, self.OnPopupSix, id=self.popupID6)

        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.popupID1, "FindItem tests")
        menu.Append(self.popupID2, "Iterate Selected")
        menu.Append(self.popupID3, "ClearAll and repopulate")
        menu.Append(self.popupID4, "DeleteAllItems")
        menu.Append(self.popupID5, "GetItem")
        menu.Append(self.popupID6, "Edit")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()


    def OnPopupOne(self, event):
        print "FindItem:", self.list.FindItem(-1, "Roxette")
        print "FindItemData:", self.list.FindItemData(-1, 11)

    def OnPopupTwo(self, event):
        index = self.list.GetFirstSelected()

        while index != -1:
            index = self.list.GetNextSelected(index)

    def OnPopupThree(self, event):
        self.list.ClearAll()
        wx.CallAfter(self.PopulateList)

    def OnPopupFour(self, event):
        self.list.DeleteAllItems()

    def OnPopupFive(self, event):
        item = self.list.GetItem(self.currentItem)
        print item.m_text, item.m_itemId, self.list.GetItemData(self.currentItem)

    def OnPopupSix(self, event):
        self.list.EditLabel(self.currentItem)

