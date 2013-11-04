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
        self.annual_pos_list = []
        self.prev_polyp = None
        self.next_polyp = None
        self.age_in_month = 0
        self.selected = False
        self.irradiance = -1
        self.growth_rate = -1
        if( parent.className == "CoralColony" ):
            self.colony = parent
        else:
            self.colony = parent.colony

    def record_annual_position(self):
        curr_pos = []
        curr_pos[:] = self.pos[:]
        self.annual_pos_list.append( curr_pos )
        #print "record annual polyp position", self.id, curr_pos, self.annual_pos_list
        return self.pos

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
        #print cos_val

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
        cos_val = max( vec[Z_INDEX], 0 )
    
        radiance_base = self.colony.config['surface_irradiance'] * math.exp( -1 * self.colony.config['attenuation_coefficient'] * depth ) #Wm-2
        
        floor_reflection = radiance_base * self.colony.config['reflection_rate']
        direct_irradiance = radiance_base * cos_val
        
        total_irradiance = floor_reflection + direct_irradiance
        self.irradiance = min( total_irradiance, self.colony.config['max_irradiance'] ) / self.colony.config['max_irradiance']
        return self.irradiance
    
        if total_irradiance > self.colony.config['max_irradiance']:
            return 1
        else:
            return total_irradiance / self.colony.config['max_irradiance']
        
        return 1
    
    def grow(self):
        irradiance = self.get_irradiance()
        growth_rate = 1 - math.exp( -1.0 * irradiance * self.colony.config['growth_constant'] ) 
        self.growth_rate = growth_rate
        self.pos += ( self.growth_vector / linalg.norm( self.growth_vector ) ) * growth_rate
        self.age_in_month += 1
        #print self.id, self.pos
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
        #rotation_matrix = matrix( [ [ math.cos( theta ), 0, math.sin( theta )] , [-1 * math.sin(theta ), 1, math.cos(theta) ], [ 0, 0, 1 ]])
        rotation_matrix = matrix( [ [ math.cos( theta ), 0, math.sin( theta )] , 
                                    [ 0, 1, 0 ],
                                    [-1 * math.sin(theta ), 0, math.cos(theta) ],
                                ] )

        
        new_vec = dot( vec, rotation_matrix )
        vec = squeeze( asarray( new_vec[0] ) )
        return vec

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
        vec /= linalg.norm( vec )
        #print p1, p2, new_loc #"center:", center, "new:", new_loc
        return new_loc, vec

    def bud_2d( self, neighboring_polyp ):

        p = CoralPolyp( self )
        p.growth_vector = ( self.growth_vector + neighboring_polyp.growth_vector ) / 2.0
        #p.pos = ( self.pos + neighboring_polyp.pos ) / 2 #
        p.pos, p.growth_vector = self.find_bud_loc_2d( neighboring_polyp )  

        for np in [ self, neighboring_polyp ]:
            theta = self.get_angle_between_vectors( p.growth_vector, np.growth_vector)
            #print "theta", theta * 180 / math.pi
            theta = theta * 1.2
            #print "theta", theta* 180 / math.pi
            new_growth_vector = self.rotate( p.growth_vector, -1.0 * theta )
            #print "divergent growth vector", ( p.growth_vector / linalg.norm( p.growth_vector ) ), ( np.growth_vector / linalg.norm( np.growth_vector ) ), ( new_growth_vector / linalg.norm( new_growth_vector ) )
            #np.growth_vector = new_growth_vector

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
    
    def recalculate_growth_vector(self):
        if not self.next_polyp:
            return
        if not self.prev_polyp:
            return
        
        p1 = self.next_polyp
        p2 = self.prev_polyp
        
        vec = p1.pos - p2.pos
        
        new_vec = self.rotate( vec, math.pi / 2 )
        self.growth_vector = new_vec / linalg.norm( new_vec )

    def get_local_center(self,neighboring_polyp):
        
        v1 = self.growth_vector
        v2 = neighboring_polyp.growth_vector
        
        p1 = self.pos
        p2 = neighboring_polyp.pos

        #print "get local center:", v1, v2, p1, p2
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
        #print "grow laterally"
        e = self.get_lower_edge_2d()
        #print e
        if e[2] < self.radius * 2:
            if not self.colony.config['allow_encrusting']:
                return

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
            #print "aa"
            z = e[2] / 2
            #print "z:", z
            sign = ( e[0] / abs( e[0] ) )
            x = e[0] + ( math.sqrt(  ( self.radius * 2 ) ** 2 - e[2] ** 2) / 2 ) * sign 
            p.pos = array( [ x, 0, z ], float )
            #temp_vec = p.pos - e
            #p.growth_vector = array( [ sign * temp_vec[2], 0, temp_vec[0] ], float ) 
            p.growth_vector = ( self.growth_vector + array( [ sign, 0, 0 ], float ) ) / 2
            #print "lateral:", self.pos, self.growth_vector, "new lateral:", p.pos, p.growth_vector
        else:
            print "lateral growth"
            center = p1.get_local_center(p2)
            v1 = p1.pos - center
            v2 = p2.pos - center
            print "center", center, "v1", v1, "v2", v2
            theta = p1.get_angle_between_vectors(v1, v2)
            print "theta", theta
            new_vec = p1.rotate( v1, theta )
            new_vec /= linalg.norm( new_vec )
            new_vec *= ( linalg.norm( v1 ) - linalg.norm( v2 ) ) + linalg.norm( v1 ) 
            new_vec = new_vec/ linalg.norm( new_vec )
            new_pos = center + new_vec
            print "new_vec", new_vec, "new_pos", new_pos
            #for i in range(3):
                #a[i] = new_vec[0,i]
                #b[i] = new_pos[0,i]
            
            #print "new:", new_vec, new_pos, a, b, center
            p.growth_vector = new_vec 
            p.pos = new_pos
            #pass
            #p.pos = array( [ , , ], float )
            print "lateral:", self.pos, self.growth_vector, "new lateral:", p.pos, p.growth_vector
        self.colony.add_polyp(p)
        #print "lateral:", p1.pos, p2.pos, p.pos
    
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

        #imgdr.line( arr, fill = color )
        #print "pos:", self.prev_pos, self.pos
        #self.prev_pos_list.append( self.prev_pos[:] )
        self.prev_pos[:] = self.pos[:]
        
        return
    
    def print_to_dc(self, dc, origin, color = "black"):

        #dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        #dc.Clear()
        dw, dh = dc.GetSize()

        dc.SetPen(wx.Pen("black", 1))
        #print "zoom 1", self.colony.config['zoom']

        if self.next_polyp:
            #print "next polyp"
            arr = []
            x1 = round( self.pos[X_INDEX] * self.colony.config['zoom'] ) + origin[0]
            y1 = round( self.pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1]
            x2 = round( self.next_polyp.pos[X_INDEX] * self.colony.config['zoom'] ) + origin[0]
            y2 = round( self.next_polyp.pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 + origin[1]
            #print "draw line"
            dc.DrawLine( x1, y1, x2, y2 )


        #print "zoom 2", self.colony.config['zoom']
        trace = []

        #print self.annual_pos_list
        for p in self.annual_pos_list:
            x1 = round( p[X_INDEX] * self.colony.config['zoom'] ) 
            y1 = round( p[Z_INDEX] * self.colony.config['zoom'] ) * -1 
            pt = wx.Point( x1, y1 )
            trace.append( pt )
        x1 = round( self.pos[X_INDEX] * self.colony.config['zoom'] ) 
        y1 = round( self.pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 
        
        pt = wx.Point( x1, y1 )
        trace.append( pt )

        #print "zoom 3", self.colony.config['zoom']

        if self.selected:
            #print "selected", self.id
            dc.SetPen(wx.Pen("red", 1))
            
        dc.DrawLines( trace, xoffset = origin[0], yoffset = origin[1] )
        
        if self.selected:
            #print "selected", self.id
            dc.SetPen(wx.Pen("red", 1))
            x1 = int( round( self.pos[X_INDEX] * self.colony.config['zoom'] ) ) + origin[0] 
            y1 = int( round( self.pos[Z_INDEX] * self.colony.config['zoom'] ) * -1 )  + origin[1]
            #print "x1, y1", x1, y1
            dc.DrawCircle( x1, y1, 5)
            txt = str( self.id ) + ": " + ", ".join( [ str( round( x * 10 ) / 10.0 ) for x in [ self.pos[X_INDEX], self.pos[Z_INDEX] ] ] )
            #print txt
            dc.DrawText( txt, x1 - 30, y1 - 50 )
            txt = ", ".join( [ str( round( x * 10 ) / 10.0 ) for x in [ self.growth_vector[X_INDEX], self.growth_vector[Z_INDEX] ] ] )
            #print txt
            dc.DrawText( txt, x1 - 30, y1 - 65 )
            irradiance = round( self.irradiance * 100 ) / 100.0 
            growth_rate = round( self.growth_rate * 100 ) / 100.0 
            dc.DrawText( str( irradiance ), x1 - 30, y1 - 80)
            dc.DrawText( str( growth_rate ), x1 - 30, y1 - 95)
            #dc.DrawLine( 10, 10, 100, 100)

        #print "zoom 4", self.colony.config['zoom']

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
        self.annual_shape = []
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
        if( float( polyp_count - self.prev_polyp_count ) / float( self.prev_polyp_count ) < self.lateral_growth_criterion ):
            self.head_polyp.grow_laterally()
            self.tail_polyp.grow_laterally()
            pass
        self.prev_polyp_count = polyp_count
        
    def record_annual_growth(self):
        p = self.head_polyp
        p.record_annual_position()
        arr = []
        pt = wx.Point( p.pos[X_INDEX], p.pos[Z_INDEX] * -1 )
        arr.append( pt)
        while p.next_polyp:
            p = p.next_polyp
            p.record_annual_position()
            pt = wx.Point( p.pos[X_INDEX] , p.pos[Z_INDEX] * -1 )
            arr.append( pt )
        self.annual_shape.append( arr )
            
    def grow(self):
        #p = self.head_polyp
        self.month += 1
        #if self.month % 1 == 0:
        if self.month % self.lateral_growth_period == 0:
            self.lateral_growth_check()

        if self.month % 12 == 0:
            self.record_annual_growth()
            
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

        for p in self.polyp_list:
            p.recalculate_growth_vector()
        
                    
        i = 1
        
        return
    
        p = self.head_polyp
        #print i, p.pos
        while p.next_polyp:
            i += 1
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
                (x,y) = pt.Get()
                zoomed_shape.append( wx.Point( x * self.config['zoom'], y * self.config['zoom'] ))
            dc.DrawLines( zoomed_shape, xoffset = origin[0], yoffset = origin[1] )
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
ID_ENCRUSTING_CHECKBOX= 1005

class ColonySimulator2DFrame( wx.Frame ):
    def __init__(self, parent, wid, name ):
        wx.Frame.__init__( self, parent, wid, name, wx.DefaultPosition, wx.Size(1024,768) )

        self.colony = CoralColony()
        
        self.interval = 10
        self.growth_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.growth_timer)
        self.growth_timer.Start(self.interval)
        
        self.ColonyView = ColonyViewControl( self, -1 )
        #self.ColonyView.SetMinSize((800,700))
        self.PlayButton = wx.Button(self, wx.ID_ANY, 'Play')
        self.ResetButton = wx.Button(self, wx.ID_ANY, 'Reset')
        #self.LoadNeighborButton = wx.Button(self, wx.ID_ANY, 'Watch')
        #self.ButtonExport = wx.Button(self, wx.ID_ANY, 'Export')
        #lb1 = wx.StaticText(self, wx.ID_ANY, '')
        #lb2 = wx.StaticText(self, wx.ID_ANY, '')
        
        self.timer_checkbox= wx.CheckBox( self, ID_TIMER_CHECKBOX, "Use Timer" )
        self.Bind( wx.EVT_CHECKBOX, self.ToggleTimer, id=ID_TIMER_CHECKBOX)
        self.encrusting_checkbox= wx.CheckBox( self, ID_ENCRUSTING_CHECKBOX, "Allow encrusting" )
        self.Bind( wx.EVT_CHECKBOX, self.ToggleEncrusting, id=ID_ENCRUSTING_CHECKBOX)
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
        sizer2.Add( self.timer_checkbox, flag=wx.EXPAND )

        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.encrusting_checkbox, flag=wx.EXPAND )

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
        self.use_timer = True 
        self.timer_checkbox.SetValue( self.use_timer )
        self.allow_encrusting = False
        self.encrusting_checkbox.SetValue( self.allow_encrusting )

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
        config['allow_encrusting'] = self.allow_encrusting

        self.colony.config = config

        x_pos = [ -9, -5, 0, 5, 9 ]
        y_pos = [ 0, 0, 0, 0, 0 ]
        z_pos = [ 0, 3, 5, 3, 0]
        grow_vector = [ array( [ -1, 0, 0 ], float ), array( [ -3, 0, 4 ], float ), array( [ 0, 0, 1 ], float ) , array( [ 3, 0, 4 ], float ),array( [ 1, 0, 0 ], float ) ]
        
        
        for i in xrange( 5 ):
            p = CoralPolyp( self.colony, pos = array( [ x_pos[i], y_pos[i], z_pos[i] ], float ) )
            p.growth_vector = grow_vector[i] / linalg.norm( grow_vector[i] )
            self.colony.add_polyp( p )
            
        #colony.prev_polyp_count = 3
        self.colony.init_colony_2d()

        self.ColonyView.SetColony( self.colony )
        self.ColonyView.Reset()
        self.ColonyView.DrawToBuffer()

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
