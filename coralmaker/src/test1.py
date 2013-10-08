'''
Created on Sep 21, 2013

@author: jikhanjung
'''

X_INDEX = 0
Y_INDEX = 1
Z_INDEX = 2
import os
import wx
#import sys
#import random
import math
from numpy import *
from opengltest import MdCanvas
import Image, ImageDraw

ATTENUATION_COEFF = 4.6 / 50.0
SURFACE_IRRADIANCE = 1361
MAX_IRRADIANCE = 100
REFLECTION_RATE = 0.05
GROWTH_CONSTANT = 10

NEIGHBOR_DISTANCE_MULTIPLIER = 2
POLYP_RADIUS = 2.5

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

        radiance_base = SURFACE_IRRADIANCE * math.exp( -1 * ATTENUATION_COEFF * depth ) #Wm-2
        
        floor_reflection = radiance_base * REFLECTION_RATE
        direct_irradiance = radiance_base * cos_val
        
        total_irradiance = floor_reflection + direct_irradiance
        
        if total_irradiance > MAX_IRRADIANCE:
            return 1
        else:
            return total_irradiance / MAX_IRRADIANCE
        
        return 1
    def get_irradiance( self ):
        depth = self.get_depth()
        vec = self.growth_vector / linalg.norm( self.growth_vector ) 
        cos_val = vec[Z_INDEX]
    
        radiance_base = SURFACE_IRRADIANCE * math.exp( -1 * ATTENUATION_COEFF * depth ) #Wm-2
        
        floor_reflection = radiance_base * REFLECTION_RATE
        direct_irradiance = radiance_base * cos_val
        
        total_irradiance = floor_reflection + direct_irradiance
        
        if total_irradiance > MAX_IRRADIANCE:
            return 1
        else:
            return total_irradiance / MAX_IRRADIANCE
        
        return 1
    
    def grow(self):
        irradiance = self.get_irradiance()
        growth_rate = 1 - math.exp( -1.0 * irradiance * GROWTH_CONSTANT ) 
        
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

        print "theta:", theta
        

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

        if sin_theta > 0:
            print "plus"
        else:
            print "minus"
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
            
            x = e[0] + ( math.sqrt(  ( self.radius * 2 ) ** 2 - e[2] ** 2) / 2 ) * ( e[0] / abs( e[0] ) )
            p.pos = array( [ x, 0, z ], float )
            temp_vec = p.pos - e
            p.growth_vector = array( [ -1 * temp_vec[2], 0, temp_vec[0] ], float ) 
            p.growth_vector = ( self.growth_vector + array( [ -1, 0, 0 ], float ) ) / 2
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
                arr.append( round( p[X_INDEX] ) + origin[0] )
                arr.append( round( p[Z_INDEX] ) * -1 + origin[1] )
            imgdr.line( arr, fill = color )

        arr = []
        for p in [ self.pos, self.prev_pos ]:
            arr.append( round( p[X_INDEX] ) + origin[0] )
            arr.append( round( p[Z_INDEX] ) * -1 + origin[1] )
        imgdr.line( arr, fill = color )
        print "pos:", self.prev_pos, self.pos
        self.prev_pos[:] = self.pos[:]
        
        return
    
        (e1, e2) = self.get_edge_2d()
        arr = []
        for e in [ e1, e2 ]:
            arr.append( round( e[X_INDEX] ) + origin[0] )
            arr.append( round( e[Z_INDEX] ) * -1 + origin[1] )
        #arr = [ e1[0], e1[2], e2[0], e2[2] ]
        #img.putpixel( ( origin[0] + int( self.pos[0] ),  origin[1] - int( self.pos[2] ) ), ( 0,0,0 ) )
        imgdr.line( arr, fill = color )


class CoralColony():
    def __init__(self, depth = 1 ):
        self.className = "CoralColony"
        self.depth = depth
        self.polyp_list = []
        self.last_id = 0
        self.month = 0
        self.prev_polyp_count = 0
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
        if( float( polyp_count - self.prev_polyp_count ) / float( self.prev_polyp_count ) < 0.01 ):
            self.head_polyp.grow_laterally()
            self.tail_polyp.grow_laterally()
            pass
        self.prev_polyp_count = polyp_count
        
    def grow(self):
        #p = self.head_polyp
        self.month += 1
        #if self.month % 1 == 0:
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


for d in [ 1, 20, 50 ]:

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
            colony.print_to_image( image )
            pass
            
    
    image.save( "colony_" + str( d ) + ".png" )
        #print colony.to_string()


ID_CORALLITE_LISTCTRL = 1001
ID_NEIGHBOR_LISTCTRL = 1002
ID_CHK_SHOW_INDEX = 1003
ID_CHK_ENHANCE_VERTICAL_GROWTH = 1004

class CoralMakerFrame( wx.Frame ):
    def __init__(self, parent, wid, name ):
        wx.Frame.__init__( self, parent, wid, name, wx.DefaultPosition, wx.Size(1024,768) )

        self.colony = CoralColony()
        self.interval = 100
        self.growth_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.growth_timer)
        self.growth_timer.Start(self.interval)
        self.show_index = False
    #self.is_growing = True
    
        self.control = MdCanvas(self)
        self.control.SetMinSize((800,600))
        self.Button1 = wx.Button(self, wx.ID_ANY, 'Play')
        self.Button2 = wx.Button(self, wx.ID_ANY, 'Reset')
        self.LoadNeighborButton = wx.Button(self, wx.ID_ANY, 'Watch')
        self.ButtonExport = wx.Button(self, wx.ID_ANY, 'Export')
#        lb1 = wx.StaticText(self, wx.ID_ANY, '')
        lb2 = wx.StaticText(self, wx.ID_ANY, '')
        
        self.chkShowIndex = wx.CheckBox( self, ID_CHK_SHOW_INDEX, "Show Index" )
        self.Bind( wx.EVT_CHECKBOX, self.ToggleShowIndex, id=ID_CHK_SHOW_INDEX )
        self.chkShowIndex.SetValue( self.show_index)  
        self.chkEnhanceVerticalGrowth = wx.CheckBox( self, ID_CHK_ENHANCE_VERTICAL_GROWTH, "Enhance Vert. Growth" )
        self.Bind( wx.EVT_CHECKBOX, self.ToggleEnhanceVerticalGrowth, id=ID_CHK_ENHANCE_VERTICAL_GROWTH )
        self.chkEnhanceVerticalGrowth.SetValue( self.show_index)  
        
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add( self.Button1, wx.ALIGN_CENTER   )
        sizer1.Add( self.Button2, wx.ALIGN_CENTER )
        sizer1.Add( self.ButtonExport, wx.ALIGN_CENTER )
    
        self.forms = dict()
        '''    
        self.neighborDistanceLabel = wx.StaticText(self, -1, 'Neigh. Dist', style=wx.ALIGN_RIGHT)
        self.forms['neighbor_distance'] = wx.TextCtrl(self, -1, str( NEIGHBOR_DISTANCE_THRESHOLD ) )
        self.neighborCountLabel = wx.StaticText(self, -1, 'No. Neighbor', style=wx.ALIGN_RIGHT)
        self.forms['neighbor_count'] = wx.TextCtrl(self, -1, str( NEIGHBOR_COUNT_THRESHOLD ) )
        self.minDistLabel = wx.StaticText(self, -1, 'Min. Dist', style=wx.ALIGN_RIGHT)
        self.forms['minimum_distance'] = wx.TextCtrl(self, -1, str( MIN_DISTANCE_FOR_DIVISION ) )
        self.reproductionLabel = wx.StaticText(self, -1, 'Reproduction rate', style=wx.ALIGN_RIGHT)
        self.forms['reproduction'] = wx.TextCtrl(self, -1, str( REPRODUCTION_RATE ) )
        self.elongationLabel = wx.StaticText(self, -1, 'Elongation rate', style=wx.ALIGN_RIGHT)
        self.forms['elongation'] = wx.TextCtrl(self, -1, str( ELONGATION_RATE ) )
        self.branchingLabel = wx.StaticText(self, -1, 'Branchingrate', style=wx.ALIGN_RIGHT)
        self.forms['branching'] = wx.TextCtrl(self, -1, str( BRANCHING_RATE ) )
        self.away1Label = wx.StaticText(self, -1, 'Away 1', style=wx.ALIGN_RIGHT)
        self.forms['away1'] = wx.TextCtrl(self, -1, str( AWAY_1 ) )
        self.away2Label = wx.StaticText(self, -1, 'Away 2', style=wx.ALIGN_RIGHT)
        self.forms['away2'] = wx.TextCtrl(self, -1, str( AWAY_2 ) )
        self.coralliteListLabel = wx.StaticText(self, -1, 'Corallite', style=wx.ALIGN_RIGHT)
        #self.coralliteListButton = wx.Button(self, -1, 'Load list' )
        self.coralliteList = wx.ListBox( self, ID_CORALLITE_LISTCTRL, choices=(),size=(100,200), style=wx.LB_SINGLE )
        self.neighborListLabel = wx.StaticText(self, -1, 'Neighbor', style=wx.ALIGN_RIGHT)
        #self.coralliteListButton = wx.Button(self, -1, 'Load list' )
        self.neighborList = wx.ListBox( self, ID_NEIGHBOR_LISTCTRL, choices=(),size=(100,200), style=wx.LB_EXTENDED )
        '''     
           
        sizer2 = wx.FlexGridSizer( 3, 3, 0, 0 )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.chkShowIndex, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.chkEnhanceVerticalGrowth, flag=wx.EXPAND )
        sizer2.Add( self.neighborDistanceLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['neighbor_distance'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.neighborCountLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['neighbor_count'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.minDistLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['minimum_distance'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.reproductionLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['reproduction'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.elongationLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['elongation'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.branchingLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['branching'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.away1Label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['away1'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.away2Label, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.forms['away2'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.coralliteListLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.coralliteList, flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.LoadNeighborButton, flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add( self.neighborListLabel, flag=wx.EXPAND )
        sizer2.Add( (10,10), flag=wx.EXPAND )
        sizer2.Add( self.neighborList, flag=wx.EXPAND | wx.ALIGN_CENTER)
    
        fs = wx.FlexGridSizer(2, 2, 10, 5)
        fs.AddGrowableCol(0)
        fs.AddGrowableCol(1)
        fs.AddGrowableRow(0)
        fs.Add( self.control, 0, wx.EXPAND )
        fs.Add( sizer2, 0, wx.ALIGN_CENTER )
        fs.Add( sizer1, 0, wx.EXPAND )
        fs.Add( lb2, 0, wx.ALIGN_CENTER )
        self.Bind( wx.EVT_BUTTON, self.OnButton1, self.Button1  )
        self.Bind( wx.EVT_BUTTON, self.OnButton2, self.Button2  )
        self.Bind( wx.EVT_BUTTON, self.OnLoadNeighbor, self.LoadNeighborButton  )
        self.Bind( wx.EVT_BUTTON, self.OnExport, self.ButtonExport  )
        #self.Bind( wx.EVT_BUTTON, self.OnLoadList, self.coralliteListButton )
        self.Bind(wx.EVT_LISTBOX, self.OnCoralliteSelected, id=ID_CORALLITE_LISTCTRL )
        self.SetSizer(fs)
        self.init_control = False
        self.is_growing = False
        self.is_watching_corallite = False
        
        self.ResetColony()
        #self.control.SetColony( self.colony )
        # self.control.ShowIndex()
        self.control.BeginAutoRotate(500)

    def ToggleShowIndex(self,event):
        self.show_index = self.chkShowIndex.GetValue()
        #print self.show_index
        if( self.show_index ):
            self.control.ShowIndex()
        else:
            self.control.HideIndex()
    
    def ToggleEnhanceVerticalGrowth(self,event):
        self.enhance_vertical_growth = self.chkEnhanceVerticalGrowth.GetValue()
        self.colony.enhance_vertical_growth = self.enhance_vertical_growth 
     
    def OnExport(self,event):
        result_str = ""
        actual_str = ""
        l_count = 0
        result_str += "3\n"
        #result_str += str( len( self.colony.corallites) )
        print "count:", l_count
        living_corallites = []
        for c in self.colony.corallites:
            if c.dead == False:
                living_corallites.append(c)
                actual_str += str( c.pos[0] ) + "\t" + str( c.pos[1] ) + "\t" + str( c.pos[2] ) + "\n"
                l_count += 1
                print "count:", l_count
        result_str += str( l_count ) + "\n"
        result_str += actual_str
        filename = "colony.dat"
        fh = file( filename, 'w' )
        fh.write( result_str )
        fh.close()
      
        os.system( '"qdelaunay Qt s i TO output.dat < colony.dat"')
        
        f = open( "output.dat", 'r' )
        data = f.read()
        f.close()
        lines = [ l.strip() for l in data.split( "\n") ]
        header = lines[0]
        lines = lines[1:]
        triangles = []
        dup_triangles = []
        for line in lines:
            if line == '': continue 
            thed = map( int, line.split(" ") )
            thed = map( lambda x: living_corallites[x].id, thed )
            print thed
            thed.sort()
            for i in range( len( thed ) ):
                t = thed[:]
                t.remove( t[i] )
                if not t in triangles and not t in dup_triangles:
                    triangles.append( t )
                    print "\t",t
                else:
                    triangles.remove( t )
                    dup_triangles.append( t )
                    print "\t", t, "duplicate!"
        triangles.sort()
        print len( triangles )
        print triangles
        """    """
        edges = []
        for tr in triangles:
            for i in range( len( tr ) ):
                e = tr[:]
                e.remove( e[i] )
                if e in edges :
                    print "\t", e, "duplicate!"
                else:
                #if self.colony.corallites[e[0]-1].get_distance(self.colony.corallites[e[1]-1] ) < 2 * float( self.forms['minimum_distance'].GetValue() ) : 
                    edges.append( e )
                    print "\t", e
        edges.sort()
        print len(edges),edges
        """    """
        self.colony.edges = edges
        return
    
      
    
    def OnCoralliteSelected(self,event):
        print "on select"
        selected_list= self.coralliteList.GetSelections()
        print selected_list
        for c in self.colony.corallites:
            c.selected = False
        for c in selected_list:
          
            self.coralliteList.GetClientData(c).selected = True
            #pass
            #c.selected = True
        return

    def OnLoadList(self,event):
        self.Button1.SetLabel( "Play" )
        self.is_growing = False
        self.LoadList()
    
    def OnLoadNeighbor(self,event):
        idx = self.coralliteList.GetSelections()
        print "load neighbor selection", idx
        c = self.coralliteList.GetClientData( idx[0] )
        print "watch colrallite", c.id
        self.WatchCorallite( c )
    
    def WatchCorallite(self, corallite ):
        if self.is_watching_corallite == True:
            self.corallite_being_watched.being_watched = False
            for c in self.colony.corallites:
                c.being_watched = False
                c.is_neighbor = False
        self.is_watching_corallite = True
        self.corallite_being_watched = corallite
        
        corallite.being_watched = True
        self.UpdateNeighborList( corallite )
    
    def UpdateNeighborList(self,corallite):
        for c in self.colony.corallites:
            c.is_neighbor = False
        self.neighborList.Clear()
        neighbors = corallite.get_neighbors()# log = True)
        #print corallite.id, corallite.pos
        for n in neighbors:
            if n.dead == False:
                n.is_neighbor = True
                self.neighborList.Append( str( n.id ), n )
                #print "  neighbor", n.id, n.is_neighbor, n.pos
      
    def LoadList(self):
        selected_list= self.coralliteList.GetSelections()
        self.coralliteList.Clear()
        for c in self.colony.corallites:
            if c.dead == False:
                lastidx = self.coralliteList.Append( str( c.id ), c )
                if c.selected == True:
                    self.coralliteList.SetSelection( lastidx )
        for idx in selected_list:
            self.coralliteList.SetSelection( idx )
    
    def OnButton1(self,event):
        if self.is_growing:
            self.is_growing = False
            self.Button1.SetLabel( "Play" )
        else:
            self.is_growing = True
            self.Button1.SetLabel( "Pause" )

    def OnButton2(self,event):
      
        self.ResetColony()
      
    def ResetColony(self):
        self.colony = CoralColony()
        self.colony.set_minimum_distance_for_division( float( self.forms['minimum_distance'].GetValue() ) )
        self.colony.set_neighbor_distance_threshold( float( self.forms['neighbor_distance'].GetValue() ) )
        self.colony.set_neighbor_count_threshold( float( self.forms['neighbor_count'].GetValue() ) )
        self.colony.set_reproduction_rate( float( self.forms['reproduction'].GetValue() ) )
        self.colony.set_elongation_rate( float( self.forms['elongation'].GetValue() ) )
        self.colony.set_branching_rate( float( self.forms['branching'].GetValue() ) )
        self.colony.set_away_1( float( self.forms['away1'].GetValue() ) )
        self.colony.set_away_2( float( self.forms['away2'].GetValue() ) )
        self.control.SetColony( self.colony )
    def OnTimer(self,event):
        if self.is_growing:
            self.colony.grow()
            self.LoadList()
            if self.is_watching_corallite == True:
                self.UpdateNeighborList( self.corallite_being_watched )

    
class CoralMakerApp(wx.App):
    def OnInit(self):
        #self.dbpath = ""
        self.frame = ''
        self.frame = CoralMakerFrame(None, -1, 'CoralMaker')
        self.frame.Show(True) 
        self.SetTopWindow(self.frame)
        return True
#app = CoralMakerApp(0)
#print sys.argv[0]
#app.MainLoop()
