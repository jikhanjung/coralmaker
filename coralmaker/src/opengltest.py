import wx
import sys
import math

from time import clock
from wx import glcanvas
import OpenGL.platform.win32
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
#from OpenGL.plugins import PlatformPlugin, FormatHandler
class MdColorScheme:
  def __init__(self):
    self.meanshape = ( 0.2, 0.2, 0.8 )
    self.meanshape_wireframe = ( 0.4, 0.4, 1.0 )
    self.selected_landmark = ( 0.6, 0.6, 0.2 )
    self.object = ( 1.0, 1.0, 0.0 )
    self.colony = ( 1.0, 1.0, 0.0 )
    self.selected_object = ( 1.0, 1.0, 0.0 )
    self.object_wireframe = ( 1.0, 1.0, 0.6)
  def convert_color(self, hexstring):
    l = len( hexstring )
    #print l
    s = hexstring[l-6:l]
    #print s
    r = s[0:2]
    g = s[2:4]
    b = s[4:6]
    #print r, g, b
    r = int( r, 16 )
    g = int( g, 16 )
    b = int( b, 16 )
    #print r, g, b
    return ( r/255.0, g/255.0, b/255.0 )

class MdCanvasBase( glcanvas.GLCanvas ):
  def __init__(self, parent):
    glcanvas.GLCanvas.__init__(self, parent, -1)
    self.init = False
    # initial mouse position
    self.color = MdColorScheme()
    self.r = 1
    self.offset = -3
    self.lm_radius = 0.1
    self.auto_rotate = False
    self.show_index = False
    self.lastx = self.x = 30
    self.lasty = self.y = 30
    self.last_xangle = 0 
    self.last_yangle = 0
    self.is_dragging = False
    self.size = None
    self.object = None
    self.colony = None
    #self.color_scheme = None
    self.init_control = False
    self.interval = 50
    self.zoom = 1.0
    self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
    self.Bind(wx.EVT_SIZE, self.OnSize)
    self.Bind(wx.EVT_PAINT, self.OnPaint)
    self.Bind( wx.EVT_LEFT_DOWN, self.OnLeftDown )
    self.Bind( wx.EVT_LEFT_UP, self.OnLeftUp )
    self.Bind( wx.EVT_MOTION, self.OnMotion )
    self.Bind( wx.EVT_MOUSEWHEEL, self.OnWheel )
    self.Bind( wx.EVT_ENTER_WINDOW, self.OnMouseEnter )


  def OnWheel(self, event ):
    rotation = event.GetWheelRotation()
    
    #print rotation
    self.zoom = self.zoom + self.zoom * 0.1 * rotation / ( ( rotation ** 2 ) ** 0.5 ) 
    #print self.zoom
    se = wx.SizeEvent()
    self.OnSize(se)
    self.Refresh(False)
    #self.OnDraw()

  def ShowIndex(self):
    self.show_index= True
    self.Refresh(False)
    #self.OnDraw()
  
  def HideIndex(self):
    self.show_index = False
    self.Refresh(False)
    #self.OnDraw()
    
  def BeginAutoRotate(self, interval=50 ):
    print "begin auto rotate"
    if self.auto_rotate:
      return
    self.auto_rotate = True
    #return
    #print "begin auto rotate interval = ", interval
    self.interval = interval
    self.rotation_timer = wx.Timer(self)
    self.Bind(wx.EVT_TIMER, self.AutoRotate, self.rotation_timer)
    self.rotation_timer.Start(self.interval)
    #self.auto_rotate = True
    #self.rotation_timer = wx.Timer(self)
    #self.Bind(wx.EVT_TIMER, self.AutoRotate, self.rotation_timer)
    #self.rotation_timer.Start(interval)
    #self.auto_rotate = True
    #self.SetSize( (400,400) )
    #self.OnDraw()
  def EndAutoRotate(self):
    #return
    #print "end auto rotate"
    self.Unbind(wx.EVT_TIMER, self.rotation_timer )
    self.auto_rotate = False
    #self.auto_rotate = False
    
  def OnLeftDown(self,event):
      #print "down"
    self.is_dragging = True
    self.CaptureMouse()
    self.x, self.y = self.lastx, self.lasty = event.GetPosition()
    #self.SetFocus()

  def OnMouseEnter(self, event):
    self.SetFocus()

  def OnLeftUp(self, event):
    #print "up"
    if self.is_dragging:
      self.is_dragging = False
      self.x, self.y = event.GetPosition()
      self.last_xangle = self.last_xangle + (self.x - self.lastx)
      self.last_yangle = self.last_yangle + self.y - self.lasty
      self.lastx = self.x
      self.lasty = self.y
      self.ReleaseMouse()
      self.AdjustObjectRotation()
      self.Refresh(False)

  def OnMotion(self,event):
    #print "onmotion"
    if self.is_dragging: #event.Dragging() and event.LeftIsDown():
      #if event.ControlDown():
      #  self.view_left 
      #else:
      #self.lastx, self.lasty = self.x, self.y
      self.x, self.y = event.GetPosition()
      #print self.lastx, self.lasty, self.x, self.y
      self.Refresh(False)
    
  def OnEraseBackground(self, event):
    #print "EraseBackground"
    pass # Do nothing, to avoid flashing on MSW.

  def OnSize(self, event):
    #print "OnSize"
    s = self.GetClientSize()
    size = self.size = s
    if self.GetContext():
      self.SetCurrent()
      glViewport(0, 0, size.width, size.height)

      # Maintain 1:1 Aspect Ratio  
      """
      the screen starts out with a glFrustum left,right,bottom,top of -0.5,0.5,-0.5,0.5
      and an aspect ratio (screen width / screen height) of 1
      """
      w = float( size.width )
      h = float( size.height )
      if self.r == 0:
        self.r = 1
      height = width = self.r
      if size.width > size.height:
        width = width * (w /h)
      elif size.height > size.width:
        height = height * (h/w)
      #print width, "x", height
      glMatrixMode(GL_PROJECTION)
      glLoadIdentity()
      #print "zoom", self.zoom
      
      znear = 0.1
      zfar = 100
      width = width / self.zoom
      height = height / self.zoom
      bottom_height = -1 * height
      top_height = height
      
      znear = ( self.offset * - 0.4 ) 
      zfar = ( self.offset * - 1.6 ) 
#      if self.superimposition_method == IDX_SBR or self.superimposition_method == IDX_BOOKSTEIN:
#        bottom_height += height
#        top_height += height
      
      glFrustum(-width, width, bottom_height, top_height, znear, zfar)
      gluLookAt( 0.0, 0.0, self.offset * -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0 )
      #print 
      #print "width height near far offset", width, height, znear, zfar, self.offset
      #print self.r
      glMatrixMode(GL_MODELVIEW) # switch back to model view
        
    event.Skip()

  def OnPaint(self, event):
    #print "OnPaint"
    dc = wx.PaintDC(self)
    self.SetCurrent()
    if not self.init:
      self.InitGL()
      self.init = True
    self.OnDraw()
        
class MdCanvas(MdCanvasBase):

  def DrawWire(self, yangle, xangle, vfrom, vto ):
    lm1 = self.colony.corallites[vfrom - 1]
    lm2 = self.colony.corallites[vto - 1]
    #print lm1.x, lm2.x
    axis_start = [0, 0, 1]
    axis_end = [lm1.pos[0]  - lm2.pos[0] , lm1.pos[1] - lm2.pos[1], lm1.pos[2] - lm2.pos[2] ]
    #print vfrom, vto, axis_start, axis_end
    angle = math.acos(axis_start[0] * axis_end[0] + axis_start[1] * axis_end[1] + axis_start[2] * axis_end[2] / ((axis_start[0] ** 2 + axis_start[1] ** 2 + axis_start[2] ** 2) ** 0.5 * (axis_end[0] ** 2 + axis_end[1] ** 2 + axis_end[2] ** 2) ** 0.5))
    angle = angle * (180 / math.pi)
    axis_rotation = [0, 0, 0]
    axis_rotation[0] = axis_start[1] * axis_end[2] - axis_start[2] * axis_end[1]
    axis_rotation[1] = axis_start[2] * axis_end[0] - axis_start[0] * axis_end[2]
    axis_rotation[2] = axis_start[0] * axis_end[1] - axis_start[1] * axis_end[0]
    if angle == 180:
      axis_rotation = [1, 0, 0]
    
    length = (axis_end[0] ** 2 + axis_end[1] ** 2 + axis_end[2] ** 2) ** 0.5
    radius = self.wire_radius
    cyl = gluNewQuadric()
    glPushMatrix()
    glLoadIdentity()
    #glTranslate(0, 0, self.offset)
    glRotatef(yangle, 1.0, 0.0, 0.0)
    glRotatef(xangle, 0.0, 1.0, 0.0)
    glTranslate(lm2.pos[0], lm2.pos[1], lm2.pos[2])
    if (angle != 0):
      glRotate(angle, axis_rotation[0], axis_rotation[1], axis_rotation[2])
    
    gluCylinder(cyl, radius, radius, length, 10, 10)
    glPopMatrix()

  def SelectLandmark(self,idx_list):
    for i in range( len( self.object.landmarks ) ):
      if i in idx_list :
        self.object.landmarks[i].selected = True
      else:
        self.object.landmarks[i].selected = False
    #print "selected idx :", idx_list
    self.Refresh(False)

  def SelectObject(self,idx_list):
    for i in range( len( self.dataset.objects ) ):
      if i in idx_list :
        self.dataset.objects[i].selected = True
      else:
        self.dataset.objects[i].selected = False
      #print self.dataset.objects[i].selected
    self.Refresh(False)

  def ToggleObjectVisibility(self, idx):
    if self.dataset.objects[idx].visible:
      self.dataset.objects[idx].visible = False 
    else:
      self.dataset.objects[idx].visible = True

  def DrawColony(self, colony, xangle, yangle, size = 0.1, color = ( 1.0, 1.0, 0.0 ), show_index = False, single_object_mode = True ):
    #print "draw colony:"#, object.objname
    original_color = color
    #i = 0
    glColor3f( color[0], color[1], color[2] )
    glLoadIdentity()
    glPushMatrix()
    #glTranslate(0, 0, self.offset)
    glRotatef(yangle, 1.0, 0.0, 0.0)
    glRotatef(xangle, 0.0, 1.0, 0.0)

#    single_object_mode = True
    if not single_object_mode:
      #print "point size, glbegin"
      glPointSize( 3 )
      glDisable(GL_LIGHTING)
      glBegin( GL_POINTS )

    for cr in colony.corallites:
      if cr.dead:
        #continue
        #glColor3f( self.color.selected_landmark[0], self.color.selected_landmark[1], self.color.selected_landmark[2] )
        glColor3f( 0.1, 0.1, 0.1 )
      elif cr.selected:
        #print cr.id, "selected"
        glColor3f( 0.5, 0.5, 0.0 )
      elif cr.is_neighbor:
        #print cr.id, "neighbor"
        glColor3f( 0.2, 0.2, 0.5 )
      else:
        glColor3f( color[0], color[1], color[2] )

      if single_object_mode:
        glPushMatrix()
        glTranslate(cr.pos[0], cr.pos[1], cr.pos[2])
        if cr.dead:
          glutSolidSphere( 0.2 , 20, 20 )        #glutSolidCube( size )
        else:
          glutSolidSphere( 0.3, 20, 20 )        #glutSolidCube( size )
        
        glPopMatrix()
      else:
        glVertex3f( cr.pos[0], cr.pos[1], cr.pos[2] )
          
      
      #if cr.selected:
      #  glColor3f( original_color[0], original_color[1], original_color[2])
      
    if not single_object_mode:
      #print "glend"
      glEnd()
      glEnable(GL_LIGHTING)

    if show_index:
      i = 0
      for cr in colony.corallites:
        i+= 1
        if cr.dead: continue
        glDisable(GL_LIGHTING)
        glColor3f(.5,.5,1.0)
        glRasterPos3f(cr.pos[0], cr.pos[1]+size*2, cr.pos[2] )
        for letter in list( str( i ) ):
          glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18,ord(letter))
        glEnable(GL_LIGHTING)
    glPopMatrix()

  def InitGL( self ):
    #print "InitGL"
    glMatrixMode(GL_PROJECTION)
    glFrustum(-1.5, 1.5, -1.5, 1.5, 1, 100.0)
    #print "width height near far offset", width, height, znear, zfar, self.offset
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    #glLightfv( GL_LIGHT0, GL_AMBIENT, ( 0.5, 0.5, 0.5, 1.0 ) )
    #glLightfv( GL_LIGHT0, GL_AMBIENT, ( 1.0, 1.0, 1.0, 1.0 ) )
    #glLightfv( GL_LIGHT0, GL_POSITION, ( 0.0, 0.0, 0.0 ) )
    #glLightfv( GL_LIGHT0, GL_SPOT_DIRECTION, ( 0.0, 0.0, -1.0 ) )
    """
    glEnable(GL_LIGHT1)
    glLightfv( GL_LIGHT1, GL_DIFFUSE, ( 1.0, 1.0, 1.0, 1.0 ) )
    glLightfv( GL_LIGHT1, GL_SPECULAR, ( 1.0, 1.0, 1.0, 1.0 ) )
    glLightfv( GL_LIGHT1, GL_POSITION, ( 0.0, 0.0, -5.0 ) )
    glLightfv( GL_LIGHT1, GL_SPOT_DIRECTION, ( 0.0, 0.0, 0.0 ) )
    glEnable(GL_LIGHT2)
    glLightfv( GL_LIGHT2, GL_DIFFUSE, ( 1.0, 1.0, 1.0, 1.0 ) )
    glLightfv( GL_LIGHT2, GL_SPECULAR, ( 1.0, 1.0, 1.0, 1.0 ) )
    glLightfv( GL_LIGHT2, GL_POSITION, ( 0.0, 5.0, -2.0 ) )
    glLightfv( GL_LIGHT2, GL_SPOT_DIRECTION, ( 0.0, 0.0, -2.0 ) )

    glEnable(GL_LIGHT3)
    glLightfv( GL_LIGHT3, GL_DIFFUSE, ( 1.0, 1.0, 1.0, 1.0 ) )
    glLightfv( GL_LIGHT3, GL_SPECULAR, ( 1.0, 1.0, 1.0, 1.0 ) )
    glLightfv( GL_LIGHT3, GL_POSITION, ( 0.0, -5.0, -2.0 ) )
    glLightfv( GL_LIGHT3, GL_SPOT_DIRECTION, ( 0.0, 0.0, -2.0 ) )
    """
    
    glEnable(GL_COLOR_MATERIAL)
    
    """ anti-aliasing """
    glEnable( GL_LINE_SMOOTH )
    glEnable( GL_POINT_SMOOTH )
    glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
    glHint( GL_LINE_SMOOTH_HINT, GL_DONT_CARE )
    
    glClearColor(0.2, 0.2, 0.2, 1.0) # set background color
    glDepthFunc(GL_LESS)
    glEnable(GL_DEPTH_TEST)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    #gluLookAt( 0.0, 0.0, 50.0, 0.0, 0.0, -100.0, 0.0, 1.0, 0.0 )
    #gluLookAt( 0.0, 0.0, self.offset * -1.0, 0.0, 0.0, -50.0, 0.0, 1.0, 0.0 )
    gluLookAt( 0.0, 0.0, self.offset * -1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0 )
    #glTranslatef(0.0, 0.0, self.offset)
    #print "offset:", self.offset
    glutInit(sys.argv)

    #self.offset = -3 # z position
    
  def AdjustObjectRotation(self):
    return
    y_angle = self.last_yangle
    self.last_yangle = 0
    x_angle = self.last_xangle
    self.last_xangle = 0
    x_angle = -1.0 * ( x_angle * math.pi ) /180 
    self.colony.rotate_3d( x_angle, 'Y')
    y_angle = ( y_angle * math.pi ) /180 
    self.colony.rotate_3d( y_angle, 'X')

  def OnDraw(self):
    # clear color and depth buffers
    #print "OnDraw"
    #begin_time = clock()
    #print "begin draw", clock()
    #print 1/0
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    yangle = self.y - self.lasty + self.last_yangle
    xangle = (self.x - self.lastx ) + self.last_xangle
    
    #dataset_begin = clock()
    #print "draw dataset", dataset_begin
    if self.colony == None:
      self.SwapBuffers()
      return

    #dataset_end = clock()
    #print "draw single object", dataset_end
    """ Draw object: """
    self.DrawColony( self.colony, xangle, yangle, self.lm_radius * 10, color=self.color.colony, show_index = self.show_index )

    if True: 
      edges = self.colony.edges #self.object.get_dataset().get_edge_list()
      #$print "on draw wireframe", wireframe.edge_list
      #print "on draw object", self.object

      for vertices in edges:
        glColor3f( self.color.object_wireframe[0], self.color.object_wireframe[1], self.color.object_wireframe[2])
        #if self.dataset == None:
        #  glColor3f( self.color.object_wireframe[0], self.color.object_wireframe[1], self.color.object_wireframe[2])
        #else:
        #  glColor3f( self.color.meanshape_wireframe[0], self.color.meanshape_wireframe[1], self.color.meanshape_wireframe[2])
        #print vertices
        vfrom = int( vertices[0] )
        vto = int( vertices[1] )
        if vfrom > len( self.colony.corallites ) or vto > len( self.colony.corallites ):
          #print "out of bound"
          continue 
        #if self.print_log:
          #print "draw wire"
        self.DrawWire(yangle, xangle, vfrom, vto )

    self.SwapBuffers()
    #end_time = clock()
    #t = end_time- begin_time
    #d = dataset_end - dataset_begin
    #print "draw:", t, d, int((d/t) *10000 )/100.0

  def AutoRotate(self,event):
    #print "auto rotate", self.is_dragging, self.auto_rotate
    if self.init_control == False:
      e = wx.SizeEvent(self.GetClientSize())
      self.OnSize( e )
      #self.SetSize( self.GetClientSize() )
      #self.GetParent().SetSize( self.GetParent().GetClientSize() )
      self.init_control = True
    if self.is_dragging or self.auto_rotate == False:
      return
    #print "rotate it!"
    #self.last_xangle += 1
    self.OnDraw()

  def SetColony(self, colony ):
    #mo.move_to_center()
    self.colony = colony
    if len( colony.corallites ) > 0 :
      self.AdjustPerspective( self.colony )
    self.SetSize( self.GetClientSize() )

  def ResetParameters(self):
    #self.zoom = 1.0
    self.OnSize( wx.SizeEvent() )
    #self.
      
  def AdjustPerspective( self, co ):
    #print "adjust perspective"
    #max_x, max_y, max_z, min_x, min_y, min_z = -999,-999,-999,999,999,999
    max_dist = 0
    for i in range( len( co.corallites ) ):
      for j in range(i+1,len(co.corallites)):
        dist = math.sqrt( ( co.corallites[i].pos[0] - co.corallites[j].pos[0] ) ** 2 +
                          ( co.corallites[i].pos[1] - co.corallites[j].pos[1] ) ** 2 +
                          ( co.corallites[i].pos[2] - co.corallites[j].pos[2] ) ** 2   )
        max_dist = max( dist, max_dist )
    """      max_x = max( lm.xcoord, max_x )
      max_y = max( lm.ycoord, max_y )
      max_z = max( lm.zcoord, max_z )
      min_x = min( lm.xcoord, min_x )
      min_y = min( lm.ycoord, min_y )
      min_z = min( lm.zcoord, min_z )
    # print max_x, min_x, max_y, min_y, max_z, min_z
    xr = max( max_x**2, min_x ** 2 ) ** 0.5
    yr = max( max_y**2, min_y ** 2 ) ** 0.5
    zr = max( max_z**2, min_z ** 2 ) ** 0.5
    r = max( xr, yr, zr )
    print "r", r
    print "x", max_x, min_x
    print "y", max_y, min_y
    print "z", max_z, min_z
    """
    if max_dist == 0:
      max_dist = 1
    self.r = max_dist * 24
    self.offset = max_dist * -60.0
    #max_diff = max( max_x - min_x, max_y - min_y, max_z - min_z )
    print "max dist", max_dist
    print "offset", self.offset
    #self.offset = -3 #max_diff * -2
    self.lm_radius = max_dist / ( 4 * len( co.corallites) )
    self.wire_radius = self.lm_radius / 2

class OpenGLTestWin( wx.Dialog ):
  def __init__(self,parent, id=-1):
    wx.Dialog.__init__(self,parent,size=(400,400))
    self.control = MdCanvas(self)
    self.control.SetMinSize((200,200))
    self.v2 = wx.Button(self, wx.ID_ANY, 'Button #2')
    lb1 = wx.StaticText(self, wx.ID_ANY, 'Video #1')
    lb2 = wx.StaticText(self, wx.ID_ANY, 'Video #2')
    fs = wx.FlexGridSizer(2, 2, 10, 5)
    fs.AddGrowableCol(0)
    fs.AddGrowableCol(1)
    fs.AddGrowableRow(0)
    fs.Add( self.control, 0, wx.EXPAND )
    fs.Add( self.v2, 0, wx.EXPAND   )
    fs.Add( lb1, 0, wx.ALIGN_CENTER )
    fs.Add( lb2, 0, wx.ALIGN_CENTER )
    self.Bind( wx.EVT_BUTTON, self.OnButton, self.v2  )
    self.SetSizer(fs)
    self.init_control = False
        # Timer
    self.Show()
    self.auto_rotate = False
    
    return
    
  def OnButton(self,e):
    if self.auto_rotate:
      self.auto_rotate = False
      self.control.EndAutoRotate()
    else:
      self.auto_rotate = True
      self.control.BeginAutoRotate()
      
  def SetObject(self, mo):
    #print "opengltestwin setobject"
    self.control.SetSingleObject( mo )
    self.control.BeginAutoRotate(50)
    self.auto_rotate = True
    
  def SetDataset(self, ds ):
    self.control.SetDataset(  ds )
    for mo in ds.objects:
      for lm in mo.landmarks:
        lm.selected = False
        
    #self.SetSize((400,400))
""" apply these color schemes later 
------
ordinary
------
FF9900
B36B00
FFE6BF
FFCC80
0033CC
00248F
BFCFFF
809FFF
3F0099
2C006B
DABFFF
B480FF
FFE400
B3A000
FFF8BF
FFF280
------
pastel
------
806640
E6DCCF
BF8630
5C73B8
405080
CFD4E6
3054BF
61458A
5A4080
D8CFE6
6B30BF
E6D973
807940
E6E3CF
BFB030
------
"""
