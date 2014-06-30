'''
Created on Mar 6, 2014

@author: jikhanjung
'''
import wx
import sys
#import random
from numpy import array, linalg
from ColonyViewer3D import ColonyViewControl
import Image

from CoralPolyp3D import CoralPolyp
from CoralColony3D import CoralColony, CoralPolygon
import CoralConfig3D 
#from ColonyViewer3D import ColonyViewControl


ID_POLYP_LISTCTRL = 1001
ID_NEIGHBOR_LISTCTRL = 1002
ID_TIMER_CHECKBOX= 1003
ID_CHK_ENHANCE_VERTICAL_GROWTH = 1004
ID_PERIPHERALBUDDING_COMBOBOX= 1005
ID_SHOWSKELETON_CHECKBOX= 1006
ID_DETERMINATEGROWTH_CHECKBOX= 1007

class ColonySimulator3DFrame( wx.Frame ):
    def __init__(self, parent, wid, name ):
        wx.Frame.__init__( self, parent, wid, name, wx.DefaultPosition, wx.Size(1024,768) )

        self.colony = CoralColony()
        
        self.interval = 10
        self.growth_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.growth_timer)
        self.growth_timer.Start(self.interval)
        self.show_skeleton = False
        
        self.ColonyView = ColonyViewControl( self )
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
        self.forms['depth'] = wx.TextCtrl(self, -1, str( CoralConfig3D.DEPTH ) )
        self.lateral_growth_period_label = wx.StaticText(self, -1, 'Lat. Growth Period', style=wx.ALIGN_RIGHT)
        self.forms['lateral_growth_period'] = wx.TextCtrl(self, -1, str( CoralConfig3D.LATERAL_GROWTH_PERIOD ) )
        self.lateral_growth_criterion_label = wx.StaticText(self, -1, 'Lat. Growth Criterion', style=wx.ALIGN_RIGHT)
        self.forms['lateral_growth_criterion'] = wx.TextCtrl(self, -1, str( CoralConfig3D.LATERAL_GROWTH_CRITERION ) )
        self.surface_irradiance_label = wx.StaticText(self, -1, 'Surface Irradiance', style=wx.ALIGN_RIGHT)
        self.forms['surface_irradiance'] = wx.TextCtrl(self, -1, str( CoralConfig3D.SURFACE_IRRADIANCE ) )
        self.attenuation_coefficient_label = wx.StaticText(self, -1, 'Attenuation Coeff.', style=wx.ALIGN_RIGHT)
        self.forms['attenuation_coefficient'] = wx.TextCtrl(self, -1, str( CoralConfig3D.ATTENUATION_COEFFICIENT) )
        self.max_irradiance_label = wx.StaticText(self, -1, 'Max Irradiance', style=wx.ALIGN_RIGHT)
        self.forms['max_irradiance'] = wx.TextCtrl(self, -1, str( CoralConfig3D.MAX_IRRADIANCE ) )
        self.reflection_rate_label = wx.StaticText(self, -1, 'Reflection Rate', style=wx.ALIGN_RIGHT)
        self.forms['reflection_rate'] = wx.TextCtrl(self, -1, str( CoralConfig3D.REFLECTION_RATE ) )
        self.growth_constant_label = wx.StaticText(self, -1, 'Growth constant', style=wx.ALIGN_RIGHT)
        self.forms['growth_constant'] = wx.TextCtrl(self, -1, str( CoralConfig3D.GROWTH_CONSTANT ) )
        self.polyp_radius_label = wx.StaticText(self, -1, 'Polyp radius', style=wx.ALIGN_RIGHT)
        self.forms['polyp_radius'] = wx.TextCtrl(self, -1, str( CoralConfig3D.POLYP_RADIUS ) )
        self.zoom_label = wx.StaticText(self, -1, 'Zoom', style=wx.ALIGN_RIGHT)
        self.forms['zoom'] = wx.TextCtrl(self, -1, str( CoralConfig3D.ZOOM ) )
        
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
        self.peripheral_budding = CoralConfig3D.ID_ROUND
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

        pos_list = [ [-2, 0, 3 ], [2, 0, 3], [ 0, 2, 3 ], [ 0, -2, 3 ] ]
        vec_list = [ array( [ -1, 0, 1 ], float ), array( [ 1, 0, 1 ], float ), array( [ 0, 1, 1 ], float ), array( [ 0, -1, 1 ], float )   ]
        tri_list = [ [ 0, 1, 2 ], [ 1, 0, 3 ] ]
        
        for i in xrange( len( pos_list ) ):
            p = CoralPolyp( self.colony, pos = array( pos_list[i], float ) )
            p.growth_vector = vec_list[i] / linalg.norm( vec_list[i] )
            self.colony.add_polyp( p )

        for i in xrange( len( tri_list ) ):
            t = CoralPolygon( self.colony, tri_list[i] )
            self.colony.add_polygon( t )

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

    
class ColonySimulator3DApp(wx.App):
    def OnInit(self):
        #self.dbpath = ""
        self.frame = ''
        self.frame = ColonySimulator3DFrame(None, -1, 'Colony Simulator 2D')
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
    


app = ColonySimulator3DApp(0)
print sys.argv[0]
app.MainLoop()
