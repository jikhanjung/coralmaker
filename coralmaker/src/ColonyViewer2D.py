#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Mar 9, 2014

@author: jikhanjung
'''

import wx
from numpy import *

class ColonyViewControl(wx.Window):
    def __init__(self, parent, wid):
        wx.Window.__init__(self, parent, wid)
        #self.SetMinSize( (700,500) )
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseEnter)
        self.zoom = 1
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.is_dragging_image = False
        self.x = self.y = self.lastx = self.lasty = 0

        w, h = self.GetSize()
        #print "dc size", w, h
        #origin = [ w / 2, h - 10 ]

        self.origin_x = int(w / 2)
        self.origin_y = h - 10
        #print "origin", self.origin_x, self.origin_y
        self.in_motion = False
        self.Reset()

    def OnSize(self, event):
        #print "on size"
        w, h = self.GetSize()
        #print "dc size", w, h
        #origin = [ w / 2, h - 10 ]

        self.origin_x = int(w / 2)
        self.origin_y = h - 10
        #print "origin", self.origin_x, self.origin_y
        self.Reset()
        self.DrawToBuffer()


    def OnRightDown(self, event):
        #print "right down"
        self.is_dragging_image = True
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = event.GetPosition()

    def OnMotion(self, event):
        self.x, self.y = event.GetPosition()
        if self.is_dragging_image:  #event.Dragging() and event.LeftIsDown():
            if not self.in_motion:
                self.in_motion = True
            self.origin_x = self.origin_x + (self.x - self.lastx)
            self.origin_y = self.origin_y + self.y - self.lasty
            self.lastx = self.x
            self.lasty = self.y
            self.DrawToBuffer()

    def OnRightUp(self, event):
        #print "right up"
        if self.is_dragging_image:
            self.EndDragging(event)

    def EndDragging(self, event):
        if self.is_dragging_image:
            self.in_motion = False
            self.is_dragging_image = False
            self.x, self.y = event.GetPosition()
            self.origin_x = self.origin_x + (self.x - self.lastx)
            self.origin_y = self.origin_y + self.y - self.lasty
            self.lastx = self.x
            self.lasty = self.y
            #print "origin", self.origin_x, self.origin_y
            self.ReleaseMouse()
            self.DrawToBuffer()


    def OnMouseEnter(self, event):
        #wx.StockCursor(wx.CURSOR_CROSS)
        self.SetFocus()

    def OnWheel(self, event):
        #print "on wheel"
        #if not self.has_image:
        #  return
        rotation = event.GetWheelRotation()
        #curr_scr_x, curr_scr_y = event.GetPosition()
        self.ModifyZoom(rotation)

    def ModifyZoom(self, rotation):
        curr_scr_x = int(self.GetSize().width / 2)
        curr_scr_y = int(self.GetSize().height / 2)

        old_zoom = self.zoom
        #curr_img_x, curr_img_y = self.ScreenXYtoImageXY( curr_scr_x, curr_scr_y )

        ZOOM_MAX = 10
        ZOOM_MIN = 0.1
        if self.zoom < 1:
            factor = 0.5
        else:
            factor = int(self.zoom)
        self.zoom += 0.1 * factor * rotation / math.fabs(rotation)
        if ZOOM_MAX < self.zoom:
            self.zoom = ZOOM_MAX
        if ZOOM_MIN > self.zoom:
            self.zoom = ZOOM_MIN
        self.DrawToBuffer()
        return

    def Reset(self):
        w, h = self.GetSize()
        #print "w,h", w, h

        self.img = img = wx.EmptyImage(w, h)
        img.SetRGBRect(wx.Rect(0, 0, w, h), 128, 128, 128)
        #self.SetImage(img, True)
        self.buffer = wx.BitmapFromImage(self.img)

    def OnPaint(self, event):
        #print "colonyview on paint"
        dc = wx.BufferedPaintDC(self, self.buffer)

    def SetColony(self, colony):
        self.colony = colony

    def DrawToBuffer(self):
        #print "prepare image", time.time() - t0

        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        dc.SetBackground(wx.GREY_BRUSH)
        dc.Clear()
        self.colony.config['zoom'] = self.zoom
        #dc.SetPen(wx.Pen("red",1))
        self.colony.print_to_dc(dc, [self.origin_x, self.origin_y])

