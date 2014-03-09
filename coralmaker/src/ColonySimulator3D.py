'''
Created on Mar 6, 2014

@author: jikhanjung
'''

X_INDEX = 0
Y_INDEX = 1
Z_INDEX = 2

ID_NONE = 0
ID_ROUND = 1
ID_ENCRUSTING = 2
ID_PLATY = 3


MAX_COLONY_SIZE = 800
import os
import wx
import sys
#import random
import math
from numpy import *
from opengltest import MdCanvas
import Image, ImageDraw

ATTENUATION_COEFFICIENT = 4.6 / 50.0
SURFACE_IRRADIANCE = 1361
MAX_IRRADIANCE = 100
REFLECTION_RATE = 0.05
GROWTH_CONSTANT = 10
LATERAL_GROWTH_PERIOD = 12
LATERAL_GROWTH_CRITERION = 0.1
NEIGHBOR_DISTANCE_MULTIPLIER = 2
POLYP_RADIUS = 2.5
DEPTH = 1
ZOOM = 1.0

class CoralColony():
    def __init__(self, depth = 1 ):
        self.className = "CoralColony"
        self.depth = depth
        self.polyp_list = []
        self.last_id = 0
        self.month = 0
        self.prev_polyp_count = 0
        self.lateral_growth_criterion = 0.01
        self.lateral_growth_period = 1 #month
        self.annual_shape = []
        self.space = zeros( ( MAX_COLONY_SIZE, MAX_COLONY_SIZE) )
        self.occupied_space = []
        self.apical_polyp_list = []
        return
        
    def add_polyp( self, p ):
        self.last_id += 1
        p.id = self.last_id
        p.prev_pos[:] = p.pos[:]
        self.polyp_list.append( p )
        return
    
    def lateral_growth_check(self):
        polyp_count = len( self.polyp_list )
        #print "polyp_count:", self.prev_polyp_count, polyp_count
        if self.config['peripheral_budding'] == ID_NONE:
            return
        if( float( polyp_count - self.prev_polyp_count ) / float( self.prev_polyp_count ) < self.config['lateral_growth_criterion'] ):
            self.head_polyp.grow_laterally()
            self.tail_polyp.grow_laterally()
            #pass
        self.prev_polyp_count = polyp_count
        
    def record_annual_growth(self):
        p = self.head_polyp
        arr = []
        pt = [ p.pos[X_INDEX], p.pos[Z_INDEX] * -1 ]
        arr.append( pt)
        while p.next_polyp:
            p = p.next_polyp
            #p.record_position()
            pt = [ p.pos[X_INDEX] , p.pos[Z_INDEX] * -1 ]
            arr.append( pt )
        self.annual_shape.append( arr )

    def grow(self):
        #p = self.head_polyp
        #if self.month % 1 == 0:
        for p in self.polyp_list:
            p.record_position()

        self.month += 1
        #print "lateral_growth_period:", self.config['lateral_growth_period']
        if self.month % self.config['lateral_growth_period'] == 0:
            self.lateral_growth_check()

        if self.month % 12 == 0:
            self.record_annual_growth()
            

        for p in self.polyp_list:
            if p.alive:
                p.grow()
        for p in self.polyp_list:
            if p.alive:
                p.check_space()

        
        for p in self.polyp_list:
            #print p.id, p.pos, len( self.polyp_list )
            if p.alive:
                if p.next_polyp:
                    if p.has_enough_space_2d( p.next_polyp ):
                        p.bud_2d( p.next_polyp )

        for p in self.polyp_list:
            if p.alive:
                p.calculate_new_growth_vector()

        for p in self.polyp_list:
            if p.alive:
                p.apply_new_growth_vector()

        for p in self.polyp_list:
            if p.alive:
                p.check_dead_or_alive()

        if len( self.apical_polyp_list ) > 0:
            print "apical polyp!"
            for p in self.polyp_list:
                if p.alive and p.apical_polyp == False:
                    min_dist = p.radius * 20
                    for ap in self.apical_polyp_list:
                        dist = p.get_distance( ap )
                        if dist < min_dist: 
                            min_dist = dist
                            
                    if min_dist == p.radius * 20:
                        p.apical_polyp = True
                        self.apical_polyp_list.append( p )

        #for p in self.polyp_list:
            #print p.id,
        #print
        
        return
    
        p = self.head_polyp
        #print i, p.pos
        while p.next_polyp:
            #i += 1
            p = p.next_polyp
            #print i, ":", p.pos
        return

    def init_colony_2d(self):
        for i in range( len( self.polyp_list ) - 1 ):
            self.polyp_list[i].next_polyp = self.polyp_list[i+1]
            self.polyp_list[i+1].prev_polyp = self.polyp_list[i]
        #for p in self.polyp_list:
        #    p.prev_pos = p.pos
        self.head_polyp = self.polyp_list[0]
        self.tail_polyp = self.polyp_list[len(self.polyp_list)-1]
        self.prev_polyp_count = len( self.polyp_list )
        
    def to_string(self):
        ret_str = ""
        p = self.head_polyp
        ret_str += p.to_string()
        while p.next_polyp:
            p = p.next_polyp
            ret_str += p.to_string()
        return ret_str

    def print_to_image(self, img ):
        (w,h) = img.size
        origin = [ w / 2, h - 10 ]
        #print "num polyps", len( self.polyp_list )
        for p in self.polyp_list:
            color = "red"
            if p == self.head_polyp or p == self.tail_polyp: 
                color = "black"
            p.print_to_image( img, origin, color )
            #print p.pos
    def print_to_dc(self, dc, origin ):
        w,h = dc.GetSize()
        #print "dc size", w, h
        #origin = [ w / 2, h - 10 ]
        for shape in self.annual_shape:
            zoomed_shape = []
            for pt in shape:
                x = pt[0]
                y = pt[1]
                zoomed_shape.append( wx.Point( x * self.config['zoom'], y * self.config['zoom'] ))
            dc.DrawLines( zoomed_shape, xoffset = origin[0], yoffset = origin[1] )
        #print "num polyps", len( self.polyp_list )
        for p in self.polyp_list:
            color = "red"
            if p == self.head_polyp or p == self.tail_polyp: 
                color = "black"
            p.print_to_dc( dc, origin, color )

        if self.config['show_skeleton']:
            for p in self.occupied_space:
                dc.SetPen(wx.Pen("yellow", 1))
                dc.DrawPoint(p[0] * self.config['zoom'] + origin[0], -1 * p[1] * self.config['zoom'] + origin[1])

'''
for d in [ 1, 20, 50 ]:

    print "depth:", d
    colony = CoralColony( depth = d )
    x_pos = [ -4.5, 0, 4.5 ]
    y_pos = [ 0, 0, 0 ]
    z_pos = [ 1.5, 4, 1.5 ]
    grow_vector = [ array( [ -3, 0, 4 ], float ), array( [ 0, 0, 1 ], float ) , array( [ 3, 0, 4 ], float ) ]
    
    
    for i in xrange( 3 ):
        p = CoralPolyp( colony, pos = array( [ x_pos[i], y_pos[i], z_pos[i] ], float ) )
        p.growth_vector = grow_vector[i]
        colony.add_polyp( p )
        
    #colony.prev_polyp_count = 3
    colony.init_colony_2d()
    #print len( colony.polyp_list )
    #print colony.to_string()
    image = Image.new( "RGB", ( 1024, 1024 ), "white" ) 
    
    for i in xrange( 100 ):
            
        print "iter:",  i, "len:", len( colony.polyp_list ) #colony.to_string()
        colony.grow()
        #print "iter:",  i, "len:", len( colony.polyp_list ) #colony.to_string()
        if i % 12 == 0:
            #print "iter:",  i, "len:", len( colony.polyp_list ) #colony.to_string()
            #colony.print_to_image( image )
            pass
            
    colony.print_to_image( image )
    image.save( "colony_" + str( d ) + ".png" )
        #print colony.to_string()
'''

class ColonyViewControl(wx.Window):
    def __init__(self,parent,wid):
        wx.Window.__init__(self,parent,wid)
        #self.SetMinSize( (700,500) )
        self.Bind( wx.EVT_PAINT, self.OnPaint )
        self.Bind( wx.EVT_MOUSEWHEEL, self.OnWheel )
        self.Bind( wx.EVT_ENTER_WINDOW, self.OnMouseEnter )
        self.zoom = 1
        self.Bind( wx.EVT_RIGHT_DOWN, self.OnRightDown )
        self.Bind( wx.EVT_RIGHT_UP, self.OnRightUp )
        self.Bind( wx.EVT_MOTION, self.OnMotion )
        self.Bind( wx.EVT_SIZE, self.OnSize )
        self.is_dragging_image = False
        self.x = self.y = self.lastx = self.lasty = 0
        
        w,h = self.GetSize()
        #print "dc size", w, h
        #origin = [ w / 2, h - 10 ]
        
        self.origin_x = int( w / 2 )
        self.origin_y = h - 10
        #print "origin", self.origin_x, self.origin_y
        self.in_motion = False
        self.Reset()
    def OnSize(self, event):
        #print "on size"
        w,h = self.GetSize()
        #print "dc size", w, h
        #origin = [ w / 2, h - 10 ]
        
        self.origin_x = int( w / 2 )
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
        if self.is_dragging_image: #event.Dragging() and event.LeftIsDown():
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

    def EndDragging(self,event):
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

    def OnWheel(self,event):
        #print "on wheel"
        #if not self.has_image:
        #  return
        rotation = event.GetWheelRotation()
        #curr_scr_x, curr_scr_y = event.GetPosition()
        self.ModifyZoom( rotation )

    def ModifyZoom(self,rotation):
        curr_scr_x = int( self.GetSize().width / 2 )
        curr_scr_y = int( self.GetSize().height / 2 )
        
        old_zoom = self.zoom
        #curr_img_x, curr_img_y = self.ScreenXYtoImageXY( curr_scr_x, curr_scr_y )
        
        ZOOM_MAX = 10
        ZOOM_MIN = 0.1
        if self.zoom < 1:
            factor = 0.5
        else:
            factor = int( self.zoom )
        self.zoom += 0.1 * factor * rotation / math.fabs( rotation ) 
        self.zoom = min( self.zoom, ZOOM_MAX )
        self.zoom = max( self.zoom, ZOOM_MIN )
        #print "zoom", self.zoom
        self.DrawToBuffer()
        return
    
        self.Refresh()

        
    def Reset(self):
        w, h = self.GetSize()
        #print "w,h", w, h
        
        self.img = img = wx.EmptyImage(w,h)
        img.SetRGBRect(wx.Rect(0,0,w,h), 128, 128, 128) 
        #self.SetImage(img, True)
        self.buffer = wx.BitmapFromImage( self.img )

    def OnPaint(self,event):
        #print "colonyview on paint"
        dc = wx.BufferedPaintDC(self, self.buffer)
        
    def SetColony(self,colony):
        self.colony = colony

    def DrawToBuffer(self):
        #print "prepare image", time.time() - t0
        
        dc = wx.BufferedDC( wx.ClientDC(self), self.buffer )
        dc.SetBackground( wx.GREY_BRUSH )
        dc.Clear()
        self.colony.config['zoom'] = self.zoom
        #dc.SetPen(wx.Pen("red",1))
        self.colony.print_to_dc( dc, [ self.origin_x, self.origin_y ] )
        

ID_POLYP_LISTCTRL = 1001
ID_NEIGHBOR_LISTCTRL = 1002
ID_TIMER_CHECKBOX= 1003
ID_CHK_ENHANCE_VERTICAL_GROWTH = 1004
ID_PERIPHERALBUDDING_COMBOBOX= 1005
ID_SHOWSKELETON_CHECKBOX= 1006
ID_DETERMINATEGROWTH_CHECKBOX= 1007

class ColonySimulator2DFrame( wx.Frame ):
    def __init__(self, parent, wid, name ):
        wx.Frame.__init__( self, parent, wid, name, wx.DefaultPosition, wx.Size(1024,768) )

        self.colony = CoralColony()
        
        self.interval = 10
        self.growth_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.growth_timer)
        self.growth_timer.Start(self.interval)
        self.show_skeleton = False
        
        self.ColonyView = ColonyViewControl( self, -1 )
        #self.ColonyView.SetMinSize((800,700))
        self.PlayButton = wx.Button(self, wx.ID_ANY, 'Play')
        self.ResetButton = wx.Button(self, wx.ID_ANY, 'Reset')
        #self.LoadNeighborButton = wx.Button(self, wx.ID_ANY, 'Watch')
        #self.ButtonExport = wx.Button(self, wx.ID_ANY, 'Export')
        #lb1 = wx.StaticText(self, wx.ID_ANY, '')
        #lb2 = wx.StaticText(self, wx.ID_ANY, '')
        
        self.determinategrowth_checkbox= wx.CheckBox( self, ID_DETERMINATEGROWTH_CHECKBOX, "Determinate growth" )
        self.Bind( wx.EVT_CHECKBOX, self.ToggleDeterminate, id=ID_DETERMINATEGROWTH_CHECKBOX)
        self.showskeleton_checkbox= wx.CheckBox( self, ID_SHOWSKELETON_CHECKBOX, "Show skeleton" )
        self.Bind( wx.EVT_CHECKBOX, self.ToggleSkeleton, id=ID_SHOWSKELETON_CHECKBOX)
        self.timer_checkbox= wx.CheckBox( self, ID_TIMER_CHECKBOX, "Use Timer" )
        self.Bind( wx.EVT_CHECKBOX, self.ToggleTimer, id=ID_TIMER_CHECKBOX)
        self.peripheralbudding_combobox= wx.ComboBox( self, ID_PERIPHERALBUDDING_COMBOBOX, "Peripheral budding", choices=[ "None", "Round", "Encrusting", "Platy" ] )
        self.Bind( wx.EVT_COMBOBOX, self.PeripheralBudding, id=ID_PERIPHERALBUDDING_COMBOBOX)
        #self.chkShowIndex.SetValue( self.show_index)  
        #self.chkEnhanceVerticalGrowth = wx.CheckBox( self, ID_CHK_ENHANCE_VERTICAL_GROWTH, "Enhance Vert. Growth" )
        #self.Bind( wx.EVT_CHECKBOX, self.ToggleEnhanceVerticalGrowth, id=ID_CHK_ENHANCE_VERTICAL_GROWTH )
        #self.chkEnhanceVerticalGrowth.SetValue( self.show_index)  
        
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add( self.PlayButton , wx.ALIGN_CENTER   )
        sizer1.Add( self.ResetButton , wx.ALIGN_CENTER )
        #sizer1.Add( self.ButtonExport, wx.ALIGN_CENTER )
    
        self.forms = dict()
        
        self.irradiance_label = wx.StaticText(self, -1, 'Irradiance', style=wx.ALIGN_RIGHT)
        self.irradiance_value = wx.TextCtrl(self, -1, '' )

        self.depth_label = wx.StaticText(self, -1, 'Depth', style=wx.ALIGN_RIGHT)
        self.forms['depth'] = wx.TextCtrl(self, -1, str( DEPTH ) )
        self.lateral_growth_period_label = wx.StaticText(self, -1, 'Lat. Growth Period', style=wx.ALIGN_RIGHT)
        self.forms['lateral_growth_period'] = wx.TextCtrl(self, -1, str( LATERAL_GROWTH_PERIOD ) )
        self.lateral_growth_criterion_label = wx.StaticText(self, -1, 'Lat. Growth Criterion', style=wx.ALIGN_RIGHT)
        self.forms['lateral_growth_criterion'] = wx.TextCtrl(self, -1, str( LATERAL_GROWTH_CRITERION ) )
        self.surface_irradiance_label = wx.StaticText(self, -1, 'Surface Irradiance', style=wx.ALIGN_RIGHT)
        self.forms['surface_irradiance'] = wx.TextCtrl(self, -1, str( SURFACE_IRRADIANCE ) )
        self.attenuation_coefficient_label = wx.StaticText(self, -1, 'Attenuation Coeff.', style=wx.ALIGN_RIGHT)
        self.forms['attenuation_coefficient'] = wx.TextCtrl(self, -1, str( ATTENUATION_COEFFICIENT) )
        self.max_irradiance_label = wx.StaticText(self, -1, 'Max Irradiance', style=wx.ALIGN_RIGHT)
        self.forms['max_irradiance'] = wx.TextCtrl(self, -1, str( MAX_IRRADIANCE ) )
        self.reflection_rate_label = wx.StaticText(self, -1, 'Reflection Rate', style=wx.ALIGN_RIGHT)
        self.forms['reflection_rate'] = wx.TextCtrl(self, -1, str( REFLECTION_RATE ) )
        self.growth_constant_label = wx.StaticText(self, -1, 'Growth constant', style=wx.ALIGN_RIGHT)
        self.forms['growth_constant'] = wx.TextCtrl(self, -1, str( GROWTH_CONSTANT ) )
        self.polyp_radius_label = wx.StaticText(self, -1, 'Polyp radius', style=wx.ALIGN_RIGHT)
        self.forms['polyp_radius'] = wx.TextCtrl(self, -1, str( POLYP_RADIUS ) )
        self.zoom_label = wx.StaticText(self, -1, 'Zoom', style=wx.ALIGN_RIGHT)
        self.forms['zoom'] = wx.TextCtrl(self, -1, str( ZOOM ) )
        
        self.polyp_list_label = wx.StaticText(self, -1, 'Polyps', style=wx.ALIGN_RIGHT)
        self.polyp_listbox = wx.ListBox( self, -1, choices=(),size=(100,200), style=wx.LB_SINGLE )

        sizer2 = wx.FlexGridSizer( 3, 3, 0, 0 )

        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.determinategrowth_checkbox, flag=wx.EXPAND )

        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.showskeleton_checkbox, flag=wx.EXPAND )

        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.timer_checkbox, flag=wx.EXPAND )

        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.peripheralbudding_combobox, flag=wx.EXPAND )

        sizer2.Add( self.depth_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['depth'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.lateral_growth_period_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['lateral_growth_period'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.lateral_growth_criterion_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['lateral_growth_criterion'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.surface_irradiance_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['surface_irradiance'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.attenuation_coefficient_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['attenuation_coefficient'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.max_irradiance_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['max_irradiance'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.reflection_rate_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['reflection_rate'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.growth_constant_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['growth_constant'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.polyp_radius_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['polyp_radius'], flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.zoom_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['zoom'], flag=wx.EXPAND | wx.ALIGN_CENTER)
 
        sizer2.Add( self.polyp_list_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.polyp_listbox, flag=wx.EXPAND | wx.ALIGN_CENTER)

        sizer2.Add( self.irradiance_label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.irradiance_value, flag=wx.EXPAND )

        fs = wx.FlexGridSizer(2, 2, 10, 5)
        fs.AddGrowableCol(0,80)
        fs.AddGrowableCol(1,20)
        fs.AddGrowableRow(0,90)
        fs.Add( self.ColonyView, 0, wx.EXPAND )
        fs.Add( sizer2, 0, wx.ALIGN_CENTER )
        fs.Add( sizer1, 0, wx.EXPAND )
        self.Bind( wx.EVT_BUTTON, self.OnPlay, self.PlayButton)
        self.Bind( wx.EVT_BUTTON, self.OnReset, self.ResetButton  )

        self.Bind(wx.EVT_LISTBOX, self.OnPolypSelected, self.polyp_listbox )
        self.SetSizer(fs)
        
        self.is_growing = False
        self.determinate_growth = False
        self.determinategrowth_checkbox.SetValue( self.determinate_growth)
        self.use_timer = True 
        self.timer_checkbox.SetValue( self.use_timer )
        self.peripheral_budding = ID_ROUND
        self.peripheralbudding_combobox.SetStringSelection( "Round" )

        self.ResetColony()
        
        #print fs.GetColWidths()
        #print fs.GetRowHeights()
        

    '''
    def OnPaint(self,evt):
        dc = wx.PaintDC(self)
        self.DrawColony( dc )

    def DrawColony( self, dc ):
        print "draw colony"
        #image = Image.new( "RGB", ( 800, 600 ), "white" ) 
        #image.save( "colony_" + str( self.colony.depth ) + ".png" )
        #dc = self.ColonyView.
        #dc = wx.ClientDC( self )
        #dc.Clear()
        #self.colony.print_to_dc( dc )
        dc.DrawLine( 100, 100, 200, 200 )
        #self.ColonyView.Refresh()
        #self.Refresh()
        #wximg = piltoimage(image)
        #self.ColonyView.SetBitmap( wximg.ConvertToBitmap())
        
        return
    '''

    def PeripheralBudding(self,event):
        idx = self.peripheralbudding_combobox.GetCurrentSelection()
        self.colony.config['peripheral_budding'] = idx
        print "peripheral budding:", idx
        return
    
    def OnPolypSelected(self,event):
        #print "on select"
        selected_list= self.polyp_listbox.GetSelections()
        #print selected_list
        for c in self.colony.polyp_list:
            c.selected = False
        for c in selected_list:
          
            self.polyp_listbox.GetClientData(c).selected = True
            #pass
            #c.selected = True
        #self.Refresh()
        self.ColonyView.DrawToBuffer()
        return
    
            
    def OnReset(self,event):
      
        self.ResetColony()
      
    def ResetColony(self):
        #self.colony = CoralColony()
        depth = int( self.forms['depth'].GetValue() )
 
        self.colony = CoralColony( depth = depth )
        
        config = {}
        config['lateral_growth_criterion'] = float( self.forms['lateral_growth_criterion'].GetValue() )
        config['lateral_growth_period'] = int( self.forms['lateral_growth_period'].GetValue() )
        config['surface_irradiance'] = float( self.forms['surface_irradiance'].GetValue() )
        config['attenuation_coefficient'] = float( self.forms['attenuation_coefficient'].GetValue() )
        config['max_irradiance'] = float( self.forms['max_irradiance'].GetValue() )
        config['reflection_rate'] = float( self.forms['reflection_rate'].GetValue() )
        config['growth_constant'] = float( self.forms['growth_constant'].GetValue() )
        config['polyp_radius'] = float( self.forms['polyp_radius'].GetValue() )
        config['zoom'] = float( self.forms['zoom'].GetValue() )
        #config['peripheral_budding'] = self.peripheral_budding
        config['show_skeleton'] = self.show_skeleton
        config['determinate_growth'] = self.determinate_growth
        #print "show skeleton on reset", self.show_skeleton
        config['peripheral_budding'] = self.peripheralbudding_combobox.GetCurrentSelection()
        #print "peripheral_budding on reset colony", config['peripheral_budding']

        self.colony.config = config
        
        #pos_list = [ [ -9, 0, 0 ], [-5, 0, 3 ], [ 0, 0, 5 ], [5, 0, 3], [9, 0, 0 ] ]
        #vec_list = [ array( [ -1, 0, 0.01 ], float ), array( [ -1, 0, 1 ], float ), array( [ 0, 0, 1 ], float ) , array( [ 1, 0, 1 ], float ),array( [ 1, 0, 0.01 ], float ) ]

        #pos_list = [ [-5, 0, 3 ], [ 0, 0, 5 ], [5, 0, 3] ]
        #vec_list = [ array( [ -1, 0, 1 ], float ), array( [ 0, 0, 1 ], float ) ,  array( [ 1, 0, 1 ], float ) ]

        pos_list = [ [-2, 0, 3 ], [2, 0, 3] ]
        vec_list = [ array( [ -1, 0, 1 ], float ), array( [ 1, 0, 1 ], float ) ]
        
        for i in xrange( len( pos_list ) ):
            p = CoralPolyp( self.colony, pos = array( pos_list[i], float ) )
            p.growth_vector = vec_list[i] / linalg.norm( vec_list[i] )
            self.colony.add_polyp( p )
        
        """
        x_pos = [ -9, -5, 0, 5, 9 ]
        y_pos = [ 0, 0, 0, 0, 0 ]
        z_pos = [ 0, 3, 5, 3, 0]
        grow_vector = [ array( [ -1, 0, 0.01 ], float ), array( [ -1, 0, 1 ], float ), array( [ 0, 0, 1 ], float ) , array( [ 1, 0, 1 ], float ),array( [ 1, 0, 0.01 ], float ) ]
        
        
        for i in xrange( 5 ):
            p = CoralPolyp( self.colony, pos = array( pos_list[i], float ) )
            p.growth_vector = grow_vector[i] / linalg.norm( grow_vector[i] )
            self.colony.add_polyp( p )
        """    
        #colony.prev_polyp_count = 3
        self.colony.init_colony_2d()
        
        #self.colony.apical_polyp_list.append( self.colony.head_polyp.next_polyp )
        #self.colony.head_polyp.next_polyp.apical_polyp = True
        

        self.ColonyView.SetColony( self.colony )
        self.ColonyView.Reset()
        self.ColonyView.DrawToBuffer()
        self.LoadList()

        '''
        self.colony.set_minimum_distance_for_division( float( self.forms['minimum_distance'].GetValue() ) )
        self.colony.set_neighbor_distance_threshold( float( self.forms['neighbor_distance'].GetValue() ) )
        self.colony.set_neighbor_count_threshold( float( self.forms['neighbor_count'].GetValue() ) )
        self.colony.set_reproduction_rate( float( self.forms['reproduction'].GetValue() ) )
        self.colony.set_elongation_rate( float( self.forms['elongation'].GetValue() ) )
        self.colony.set_branching_rate( float( self.forms['branching'].GetValue() ) )
        self.colony.set_away_1( float( self.forms['away1'].GetValue() ) )
        self.colony.set_away_2( float( self.forms['away2'].GetValue() ) )
        '''

        #self.ColonyView.SetColony( self.colony )

    def GrowColony(self):
        self.colony.grow()
        self.ColonyView.DrawToBuffer()
        self.LoadList()

    def OnTimer(self,event):
        if self.is_growing:
            self.GrowColony()

    def ToggleTimer(self,event):
        self.use_timer = self.timer_checkbox.GetValue()

    def ToggleDeterminate(self,event):
        self.determinate_growth= self.determinategrowth_checkbox.GetValue()

    def ToggleSkeleton(self,event):
        #print "toggle skeleton"
        self.show_skeleton= self.showskeleton_checkbox.GetValue()
        self.colony.config['show_skeleton'] = self.show_skeleton
        self.ColonyView.DrawToBuffer()
        #print "show skeleton 1", self.show_skeleton

    def ToggleEncrusting(self,event):
        self.allow_encrusting = self.encrusting_checkbox.GetValue()

    def OnPlay(self,event):
        if self.use_timer:
            if self.is_growing:
                self.is_growing = False
                self.PlayButton.SetLabel( "Play" )
            else:
                self.is_growing = True
                self.PlayButton.SetLabel( "Pause" )
        else:
            self.GrowColony()
            #    self.UpdateNeighborList( self.corallite_being_watched )

    def LoadList(self):
        #print "load list"
        self.polyp_listbox.Clear()
        h = self.colony.head_polyp
        self.polyp_listbox.Append( str( h.id ), h )
        while h.next_polyp:
            h = h.next_polyp
            self.polyp_listbox.Append( str( h.id ), h )

    
class ColonySimulator2DApp(wx.App):
    def OnInit(self):
        #self.dbpath = ""
        self.frame = ''
        self.frame = ColonySimulator2DFrame(None, -1, 'Colony Simulator 2D')
        self.frame.Show(True) 
        self.SetTopWindow(self.frame)
        return True

def piltoimage(pil,alpha=True):
    """Convert PIL Image to wx.Image."""
    if alpha:
        #print "alpha 1", clock()
        image = apply( wx.EmptyImage, pil.size )
        #print "alpha 2", clock()
        image.SetData( pil.convert( "RGB").tostring() )
        #print "alpha 3", clock()
        image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])
        #print "alpha 4", clock()
    else:
        #print "no alpha 1", clock()
        image = wx.EmptyImage(pil.size[0], pil.size[1])
        #print "no alpha 2", clock()
        new_image = pil.convert('RGB')
        #print "no alpha 3", clock()
        data = new_image.tostring()
        #print "no alpha 4", clock()
        image.SetData(data)
        #print "no alpha 5", clock()
    #print "pil2img", image.GetWidth(), image.GetHeight()
    return image

def imagetopil(image):
    """Convert wx.Image to PIL Image."""
    #print "img2pil", image.GetWidth(), image.GetHeight()
    pil = Image.new('RGB', (image.GetWidth(), image.GetHeight()))
    pil.fromstring(image.GetData())
    return pil
    


app = ColonySimulator2DApp(0)
print sys.argv[0]
app.MainLoop()
