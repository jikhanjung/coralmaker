'''
Created on Sep 21, 2013

@author: jikhanjung
'''

import os
import wx
import sys
import random
import math
from numpy import *
from opengltest import MdCanvas

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
        self.prev_polyp = None
        self.next_polyp = None
        if( parent.className == "CoralColony" ):
            self.colony = parent
        else:
            self.colony = parent.colony

    def bud(self):
        return
    
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
        
    def grow(self):
        self.pos += ( self.grow_vector / linalg.norm( self.grow_vector ) )  
        return
    
    def has_enough_space(self):
        if self.prev_polyp:
            dist = self.get_distance( self.prev_polyp ) 
            if dist > self.radius * 2:
                p = CoralPolyp( self )
                p.pos = ( self.pos + self.prev_polyp.pos ) / 2.0 
                p.grow_vector = ( self.grow_vector + self.prev_polyp.grow_vector ) / 2.0
                self.prev_polyp.next_polyp = p
                p.prev_polyp = self.prev_polyp
                self.prev_polyp = p
                p.next_polyp = self
                self.colony.add_polyp( p )
        if self.next_polyp:
            dist = self.get_distance( self.next_polyp )
            if dist > self.radius * 2:
                p = CoralPolyp( self )
                p.pos = ( self.pos + self.next_polyp.pos ) / 2.0 
                p.grow_vector =  ( self.grow_vector + self.next_polyp.grow_vector ) / 2.0
                self.next_polyp.prev_polyp = p
                p.next_polyp = self.next_polyp
                self.next_polyp = p
                p.prev_polyp = self
                self.colony.add_polyp( p )
            
        return False
    def to_string(self):
        ret_str = ""
        ret_str += "[" + ", ".join( [ str( int( x * 10 ) / 10.0 ) for x in self.pos ] ) + "] / "
        ret_str += "[" + ", ".join( [ str( int( x * 10 ) / 10.0 ) for x in self.grow_vector ] ) + "]\n"
        return ret_str
    
class CoralColony():
    def __init__(self, depth = 1 ):
        self.className = "CoralColony"
        self.depth = depth
        self.polyp_list = []
        self.last_id = 0
        return
        
    def add_polyp( self, p ):
        self.last_id += 1
        p.id = self.last_id
        self.polyp_list.append( p )
        return
    
    def grow(self):
        for p in self.polyp_list:
            p.grow()
            if p.has_enough_space():
                p.bud()
        return

    def init_neighbor_2d(self):
        for i in range( len( self.polyp_list ) - 1 ):
            self.polyp_list[i].next_polyp = self.polyp_list[i+1]
            self.polyp_list[i+1].prev_polyp = self.polyp_list[i]
        self.head_polyp = self.polyp_list[0]
        self.tail_polyp = self.polyp_list[len(self.polyp_list)-1]
    def to_string(self):
        ret_str = ""
        p = self.head_polyp
        ret_str += p.to_string()
        while p.next_polyp:
            p = p.next_polyp
            ret_str += p.to_string()
        return ret_str
        

colony = CoralColony()
x_pos = [ -4.5, 0, 4.5 ]
y_pos = [ 0, 0, 0 ]
z_pos = [ 1.5, 3, 1.5 ]
grow_vector = [ array( [ -3, 0, 4 ], float ), array( [ 0, 0, 1 ], float ) , array( [ 3, 0, 4 ], float ) ]


for i in xrange( 3 ):
    p = CoralPolyp( colony, pos = array( [ x_pos[i], y_pos[i], z_pos[i] ], float ) )
    p.grow_vector = grow_vector[i]
    colony.add_polyp( p )

colony.init_neighbor_2d()
#print len( colony.polyp_list )
#print colony.to_string()

for i in xrange( 100 ):
    print len( colony.polyp_list )
    colony.grow()
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