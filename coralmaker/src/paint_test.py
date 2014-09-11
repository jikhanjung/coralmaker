#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 10, 2013

@author: jikhanjung
'''
import wx


class DrawButton(wx.Button):
    def __init__(self, parent, title):
        wx.Button.__init__(self, parent, title)


# self.Bind( wx.EVT_PAINT, self.OnPaint )
#    def OnPaint(self, e):
#        dc = wx.PaintDC( self )
#        dc.DrawLine(5, 5, 50, 10)

class Example(wx.Frame):
    def __init__(self, parent, title):
        super(Example, self).__init__(parent, title=title,
                                      size=(250, 150))

        self.Bind(wx.EVT_PAINT, self.OnPaint)

        #sizer = wx.BoxSizer()
        btn1 = wx.Button(self, -1, label="a", pos=(10, 10), size=(20, 20))
        btn1.SetSize((50, 50 ))
        #btn2 = DrawButton(self,-1,"def")
        #btn2.SetMaxSize( (20, 20 ))
        #sizer.Add( btn )
        #self.SetSizer( sizer )
        #sizer.Fit()
        #self.Centre()

    def OnPaint(self, e):
        dc = wx.PaintDC(self)
        dc.DrawLine(50, 60, 190, 60)


if __name__ == '__main__':
    app = wx.App()
    app.frame = Example(None, 'Line')
    app.frame.Show()
    app.MainLoop()