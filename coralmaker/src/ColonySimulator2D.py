'''
Created on Sep 21, 2013

@author: jikhanjung
'''

X_INDEX = 0
Y_INDEX = 1
Z_INDEX = 2
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
class CoralPolyp():
    def __init__(self, parent, pid=-1, pos = array( [0,0,0], float ), radius = POLYP_RADIUS, height = 1 ):
        self.id = pid
        self.className = "CoralPolyp"
        self.x = 0
        self.y = 0
        self.z = 0
        self.radius = radius
        self.height = height
        self.neighbor_list = []
        self.triangle_list = []
        self.pos = pos
        self.prev_pos = array( [0,0,0], float)
        self.prev_pos_list = []
        self.prev_polyp = None
        self.next_polyp = None
        self.age_in_month = 0
        if( parent.className == "CoralColony" ):
            self.colony = parent
        else:
            self.colony = parent.colony

    def scan_neighbors( self ):
        polyp_list = self.colony.polyp_list
        for polyp in polyp_list:
            if polyp.id == self.id:
                pass
            dist = self.get_distance( polyp )
            if dist >= NEIGHBOR_DISTANCE_MULTIPLIER * self.radius: 
                pass
            else:
                self.neighbor_list.append( polyp )
                
    def get_distance(self, c ):
        dist = linalg.norm( self.pos - c.pos )
        return dist
    
    def get_depth(self):
        return self.colony.depth
        
    def _get_irradiance(self):
        depth = self.get_depth()
        vec = self.grow_vector / linalg.norm( self.grow_vector ) 
        cos_val = vec[Z_INDEX]
        print cos_val

        radiance_base = self.config['surface_irradiance'] * math.exp( -1 * self.config['attenuation_coefficient'] * depth ) #Wm-2
        
        floor_reflection = radiance_base * self.config['reflection_rate']
        direct_irradiance = radiance_base * cos_val
        
        total_irradiance = floor_reflection + direct_irradiance
        
        if total_irradiance > self.config['max_irradiance']:
            return 1
        else:
            return total_irradiance / self.config['max_irradiance']
        
        return 1
    def get_irradiance( self ):
        depth = self.get_depth()
        vec = self.growth_vector / linalg.norm( self.growth_vector ) 
        cos_val = vec[Z_INDEX]
    
        radiance_base = self.colony.config['surface_irradiance'] * math.exp( -1 * self.colony.config['attenuation_coefficient'] * depth ) #Wm-2
        
        floor_reflection = radiance_base * self.colony.config['reflection_rate']
        direct_irradiance = radiance_base * cos_val
        
        total_irradiance = floor_reflection + direct_irradiance
        
        if total_irradiance > self.colony.config['max_irradiance']:
            return 1
        else:
            return total_irradiance / self.colony.config['max_irradiance']
        
        return 1
    
    def grow(self):
        irradiance = self.get_irradiance()
        growth_rate = 1 - math.exp( -1.0 * irradiance * self.colony.config['growth_constant'] ) 
        
        self.pos += ( self.growth_vector / linalg.norm( self.growth_vector ) ) * growth_rate
        self.age_in_month += 1
        print self.id, self.pos
        return
    
    def has_enough_space_2d(self, neighboring_polyp ):
        dist = self.get_distance( neighboring_polyp ) 
        if dist > self.radius * 2:
            return True
        return False
    
    def find_bud_loc_2d_new(self, neighboring_polyp):
        v1 = self.growth_vector
        v2 = neighboring_polyp.growth_vector

        theta = self.get_angle_between_growth_vectors( v1, v2 )

        #print "theta:", theta
        

        cos_theta = dot( v1, v2 ) / ( linalg.norm( v1 ) * linalg.norm( v2 ) )#p1.
        theta = math.acos( cos_theta )
        new_growth_vector = self.rotate( v1, theta )
        
    def rotate(self,vec,theta):
        rotation_matrix = matrix( [ [ math.cos( theta ), 0, math.sin( theta )] , [-1 * math.sin(theta ), 1, math.cos(theta) ], [ 0, 0, 1 ]])
        new_vec = dot( vec, rotation_matrix )
        return new_vec

    def get_angle_between_vectors(self, v1, v2 ):
        
        cross_product = cross( v1, v2 )
        sin_theta = cross_product[Y_INDEX] / ( linalg.norm( v1 ) * linalg.norm( v2 ) )

        #if sin_theta > 0:
            #print "plus"
        #else:
            #print "minus"
        theta = math.asin( sin_theta )
        return theta
              

    def find_bud_loc_2d( self, neighboring_polyp ):
       
        p1 = self.pos
        p2 = neighboring_polyp.pos

        center = self.get_local_center( neighboring_polyp )
        #print p1, p2, "center:", center
        #radius = linalg.norm( p1 - center )
        vec_len = ( linalg.norm( p1 - center ) + linalg.norm( p2 - center ) ) / 2
        vec = ( ( p1 - center ) / linalg.norm( p1 - center )  + ( p2 - center ) / linalg.norm( p1 - center ) ) / 2
        new_loc = center + ( vec / linalg.norm( vec ) ) * vec_len
        
        #print p1, p2, new_loc #"center:", center, "new:", new_loc
        return new_loc, vec
    
    def bud_2d( self, neighboring_polyp ):

        p = CoralPolyp( self )
        p.growth_vector = ( self.growth_vector + neighboring_polyp.growth_vector ) / 2.0
        #p.pos = ( self.pos + neighboring_polyp.pos ) / 2 #
        p.pos, p.growth_vector = self.find_bud_loc_2d( neighboring_polyp )  
        
        if self.prev_polyp == neighboring_polyp:
            neighboring_polyp.next_polyp = p
            p.prev_polyp = neighboring_polyp
            self.prev_polyp = p
            p.next_polyp = self
        else:
            neighboring_polyp.prev_polyp = p
            p.next_polyp = neighboring_polyp
            self.next_polyp = p
            p.prev_polyp = self

        self.colony.add_polyp( p )            
        
        return

    def get_local_center(self,neighboring_polyp):
        
        v1 = self.growth_vector
        v2 = neighboring_polyp.growth_vector
        
        p1 = self.pos
        p2 = neighboring_polyp.pos

        print "get local center:", v1, v2, p1, p2
        a1 = -1 * v1[2]
        b1 = v1[0]
        c1 = a1 * p1[0] + b1 * p1[2]
        a2 = -1 * v2[2]
        b2 = v2[0]
        c2 = a2 * p2[0] + b2 * p2[2]
        
        arr_a = array( [ [a1, b1], [a2, b2]] )
        arr_b = array( [ c1, c2 ] )
        arr_x = linalg.solve( arr_a, arr_b )
        
        center = array( [ arr_x[0], 0, arr_x[1] ], float)
        return center
        

    def grow_laterally(self):
        print "grow laterally"
        p = CoralPolyp( self )

        if self.next_polyp: # head
            p1 = self
            p2 = self.next_polyp

            p.next_polyp = self
            self.prev_polyp = p
            self.colony.head_polyp = p
        else: #tail
            p1 = self 
            p2 = self.prev_polyp

            p.prev_polyp = self
            self.next_polyp = p
            self.colony.tail_polyp = p

        e = self.get_lower_edge_2d()
        #print e
        if e[2] < self.radius * 2:
            print "aa"
            z = e[2] / 2
            sign = ( e[0] / abs( e[0] ) )
            x = e[0] + ( math.sqrt(  ( self.radius * 2 ) ** 2 - e[2] ** 2) / 2 ) * sign 
            p.pos = array( [ x, 0, z ], float )
            #temp_vec = p.pos - e
            #p.growth_vector = array( [ sign * temp_vec[2], 0, temp_vec[0] ], float ) 
            p.growth_vector = ( self.growth_vector + array( [ sign, 0, 0 ], float ) ) / 2
        else:
            print "bb"
            center = p1.get_local_center(p2)
            v1 = p1.pos - center
            v2 = p2.pos - center
            theta = p1.get_angle_between_vectors(v1, v2)
            new_vec = p1.rotate( v1, theta )
            new_vec /= linalg.norm( new_vec )
            new_vec *= ( linalg.norm( v1 ) - linalg.norm( v2 ) ) + linalg.norm( v1 ) 
            new_vec = new_vec
            new_pos = center + new_vec
            a = array( [0,0,0],float)
            b = array( [0,0,0],float)
            a[:] = new_vec[0,:]
            b[:] = new_pos[0,:]
            #for i in range(3):
                #a[i] = new_vec[0,i]
                #b[i] = new_pos[0,i]
            
            print "new:", new_vec, new_pos, a, b, center
            p.growth_vector = a
            p.pos = b
            #pass
            #p.pos = array( [ , , ], float )
        self.colony.add_polyp(p)
        print "lateral:", p1.pos, p2.pos, p.pos
    
    def get_edge_2d(self):
        center = self.pos
        vec = self.growth_vector
        lateral_vec = array( [ vec[2] * -1, 0, vec[0] ], float )
        lateral_vec_u = lateral_vec / linalg.norm( lateral_vec )
        edge1 = center + lateral_vec_u * self.radius
        edge2 = center - lateral_vec_u * self.radius
        return ( edge1, edge2 )
    
    def get_lower_edge_2d(self):
        (e1,e2) = self.get_edge_2d()
        if e1[2] < e2[2]:
            return e1
        else:
            return e2    
    def to_string(self):
        ret_str = ""
        ret_str += "[" + ", ".join( [ str( round( x * 10 ) / 10.0 ) for x in self.pos ] ) + "] / "
        ret_str += "[" + ", ".join( [ str( round( x * 10 ) / 10.0 ) for x in self.growth_vector ] ) + "]\n"
        return ret_str

    def print_to_image(self, img, origin, color = "black"):
        
        imgdr = ImageDraw.Draw( img )
        if self.next_polyp:
            arr = []
            for p in [ self.pos, self.next_polyp.pos ]:
                arr.append( round( p[X_INDEX] * self.colony.config['zoom'] ) + origin[0] )
                arr.append( round( p[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1] )
            imgdr.line( arr, fill = color )

        arr = []
        for p in [ self.pos, self.prev_pos ]:
            arr.append( round( p[X_INDEX] * self.colony.config['zoom'] ) + origin[0] )
            arr.append( round( p[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1] )
        #imgdr.line( arr, fill = color )
        #print "pos:", self.prev_pos, self.pos
        self.prev_pos_list.append( self.prev_pos[:] )
        self.prev_pos[:] = self.pos[:]
        
        return
    
    def print_to_dc(self, dc, origin, color = "black"):

        #dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        #dc.Clear()
        dw, dh = dc.GetSize()

        dc.SetPen(wx.Pen("black", 1))

        if self.next_polyp:
            print "next polyp"
            arr = []
            x1 = round( self.pos[X_INDEX] * self.colony.config['zoom'] ) + origin[0]
            y1 = round( self.pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1]
            x2 = round( self.next_polyp.pos[X_INDEX] * self.colony.config['zoom'] ) + origin[0]
            y2 = round( self.next_polyp.pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1]
            print "draw line"
            dc.DrawLine( x1, y1, x2, y2 )

        x1 = round( self.pos[X_INDEX] * self.colony.config['zoom'] ) + origin[0]
        y1 = round( self.pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1]
        x2 = round( self.prev_pos[X_INDEX] * self.colony.config['zoom'] ) + origin[0]
        y2 = round( self.prev_pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1]
        #dc.DrawLine( x1, y1, x2, y2 )
        
        self.prev_pos_list.append( self.prev_pos[:] )
        self.prev_pos[:] = self.pos[:]
        
        return



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
        return
        
    def add_polyp( self, p ):
        self.last_id += 1
        p.id = self.last_id
        p.prev_pos[:] = p.pos[:]
        self.polyp_list.append( p )
        return
    
    def lateral_growth_check(self):
        polyp_count = len( self.polyp_list )
        print "polyp_count:", self.prev_polyp_count, polyp_count
        if( float( polyp_count - self.prev_polyp_count ) / float( self.prev_polyp_count ) < self.lateral_growth_criterion ):
            self.head_polyp.grow_laterally()
            self.tail_polyp.grow_laterally()
            pass
        self.prev_polyp_count = polyp_count
        
    def grow(self):
        #p = self.head_polyp
        self.month += 1
        #if self.month % 1 == 0:
        if self.month % self.lateral_growth_period == 0:
            self.lateral_growth_check()

        for p in self.polyp_list:
            p.grow()
        
        for p in self.polyp_list:
            #print p.id, p.pos, len( self.polyp_list )
            if p.prev_polyp:
                if p.has_enough_space_2d( p.prev_polyp ):
                    p.bud_2d( p.prev_polyp )
            if p.next_polyp:
                if p.has_enough_space_2d( p.next_polyp ):
                    p.bud_2d( p.next_polyp )
                    
        i = 1
        
        return
    
        p = self.head_polyp
        print i, p.pos
        while p.next_polyp:
            i += 1
            p = p.next_polyp
            print i, ":", p.pos
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
        print "num polyps", len( self.polyp_list )
        for p in self.polyp_list:
            color = "red"
            if p == self.head_polyp or p == self.tail_polyp: 
                color = "black"
            p.print_to_image( img, origin, color )
            #print p.pos
    def print_to_dc(self, dc ):
        w,h = dc.GetSize()
        print "dc size", w, h
        origin = [ w / 2, h - 10 ]
        #print "num polyps", len( self.polyp_list )
        for p in self.polyp_list:
            color = "red"
            if p == self.head_polyp or p == self.tail_polyp: 
                color = "black"
            p.print_to_dc( dc, origin, color )

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
    def __init__(self,parent,id):
        wx.Window.__init__(self,parent,id)
        self.Bind( wx.EVT_PAINT, self.OnPaint )
        self.img = img = wx.EmptyImage(640,480)
        img.SetRGBRect(wx.Rect(0,0,640,480), 128, 128, 128) 
        #self.SetImage(img, True)
        self.buffer = wx.BitmapFromImage( self.img )

    def OnPaint(self,event):
        print "colonyview on paint"
        dc = wx.BufferedPaintDC(self, self.buffer)
        
    def SetColony(self,colony):
        self.colony = colony

    def DrawToBuffer(self):
        #print "prepare image", time.time() - t0
        
        dc = wx.BufferedDC( wx.ClientDC(self), self.buffer )
        dc.SetBackground( wx.GREY_BRUSH )
        dc.Clear()
        #dc.SetPen(wx.Pen("red",1))
        self.colony.print_to_dc( dc )
        

ID_POLYP_LISTCTRL = 1001
ID_NEIGHBOR_LISTCTRL = 1002
ID_CHK_SHOW_INDEX = 1003
ID_CHK_ENHANCE_VERTICAL_GROWTH = 1004

class ColonySimulator2DFrame( wx.Frame ):
    def __init__(self, parent, wid, name ):
        wx.Frame.__init__( self, parent, wid, name, wx.DefaultPosition, wx.Size(1024,768) )

        self.colony = CoralColony()
        
        self.interval = 100
        self.growth_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.growth_timer)
        self.growth_timer.Start(self.interval)
        
        self.ColonyView = ColonyViewControl( self, -1 )
        self.ColonyView.SetMinSize((800,600))
        self.PlayButton = wx.Button(self, wx.ID_ANY, 'Play')
        self.ResetButton = wx.Button(self, wx.ID_ANY, 'Reset')
        #self.LoadNeighborButton = wx.Button(self, wx.ID_ANY, 'Watch')
        #self.ButtonExport = wx.Button(self, wx.ID_ANY, 'Export')
        #lb1 = wx.StaticText(self, wx.ID_ANY, '')
        #lb2 = wx.StaticText(self, wx.ID_ANY, '')
        
        #self.chkShowIndex = wx.CheckBox( self, ID_CHK_SHOW_INDEX, "Show Index" )
        #self.Bind( wx.EVT_CHECKBOX, self.ToggleShowIndex, id=ID_CHK_SHOW_INDEX )
        #self.chkShowIndex.SetValue( self.show_index)  
        #self.chkEnhanceVerticalGrowth = wx.CheckBox( self, ID_CHK_ENHANCE_VERTICAL_GROWTH, "Enhance Vert. Growth" )
        #self.Bind( wx.EVT_CHECKBOX, self.ToggleEnhanceVerticalGrowth, id=ID_CHK_ENHANCE_VERTICAL_GROWTH )
        #self.chkEnhanceVerticalGrowth.SetValue( self.show_index)  
        
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add( self.PlayButton , wx.ALIGN_CENTER   )
        sizer1.Add( self.ResetButton , wx.ALIGN_CENTER )
        #sizer1.Add( self.ButtonExport, wx.ALIGN_CENTER )
    
        self.forms = dict()
        
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

        fs = wx.FlexGridSizer(2, 2, 10, 5)
        fs.AddGrowableCol(0)
        fs.AddGrowableCol(1)
        fs.AddGrowableRow(0)
        fs.Add( self.ColonyView, 0, wx.EXPAND )
        fs.Add( sizer2, 0, wx.ALIGN_CENTER )
        fs.Add( sizer1, 0, wx.EXPAND )
        self.Bind( wx.EVT_BUTTON, self.OnPlay, self.PlayButton)
        self.Bind( wx.EVT_BUTTON, self.OnReset, self.ResetButton  )

        self.Bind(wx.EVT_LISTBOX, self.OnPolypSelected, self.polyp_listbox )
        self.SetSizer(fs)
        
        self.ResetColony()
        self.is_growing = False
        #self.control.SetColony( self.colony )
        # self.control.ShowIndex()
        #self.control.BeginAutoRotate(500)
        #self.InitBuffer()

        #self.Bind( wx.EVT_PAINT, self.OnPaint )
        #dc = wx.ClientDC( self )
        #dc.DrawLine( 100, 100, 200, 200 )

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
    def OnPolypSelected(self,event):
        print "on select"
        selected_list= self.polyp_listbox.GetSelections()
        print selected_list
        for c in self.colony.polyp_list:
            c.selected = False
        for c in selected_list:
          
            self.polyp_listbox.GetClientData(c).selected = True
            #pass
            #c.selected = True
        return
    
    def OnPlay(self,event):
        if self.is_growing:
            self.is_growing = False
            self.PlayButton.SetLabel( "Play" )
        else:
            self.is_growing = True
            self.PlayButton.SetLabel( "Pause" )

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

        self.colony.config = config

        x_pos = [ -4.5, 0, 4.5 ]
        y_pos = [ 0, 0, 0 ]
        z_pos = [ 1.5, 4, 1.5 ]
        grow_vector = [ array( [ -3, 0, 4 ], float ), array( [ 0, 0, 1 ], float ) , array( [ 3, 0, 4 ], float ) ]
        
        
        for i in xrange( 3 ):
            p = CoralPolyp( self.colony, pos = array( [ x_pos[i], y_pos[i], z_pos[i] ], float ) )
            p.growth_vector = grow_vector[i]
            self.colony.add_polyp( p )
            
        #colony.prev_polyp_count = 3
        self.colony.init_colony_2d()
        self.ColonyView.SetColony( self.colony )
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

    def OnTimer(self,event):
        if self.is_growing:
            self.colony.grow()
            self.ColonyView.DrawToBuffer()
            #self.DrawColony()
            
            #print "refresh"
            #self.Refresh()
            #self.ColonyView

            #self.ColonyView.

            self.LoadList()
        #self.OnPaint(None)
            #    self.UpdateNeighborList( self.corallite_being_watched )
    def LoadList(self):
        print "load list"
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
