#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import random
import math

import wx
from numpy import *

from opengltest import MdCanvas


NEIGHBOR_DISTANCE_THRESHOLD = 5
NEIGHBOR_COUNT_THRESHOLD = 4
MIN_DISTANCE_FOR_DIVISION = 5
AWAY_1 = 1.0
AWAY_2 = 1.0
REPRODUCTION_RATE = 0.1
ELONGATION_RATE = 0.1
BRANCHING_RATE = 0.1
MOVE_RATIO_PER_TICK = 0.005


class Corallite():
    def __init__(self, parent, id=-1, pos=array([0, 0, 0], float)):
        self.id = id
        self.className = "Corallite"
        self.x = 0
        self.y = 0
        self.z = 0
        self.radius = 1
        self.height = 1
        self.upwardVector = array([0, 0, 0.1], float)
        self.lateralVector = array([0, 0, 0], float)
        self.move_ratio_per_tick = MOVE_RATIO_PER_TICK
        self.dead = False
        self.trace = None
        self.selected = False
        self.is_neighbor = False
        self.connected_neighbor = []
        self.move_vector = array([0, 0, 0], float)
        if parent.className == "Colony":
            self.colony = parent
        else:
            self.parent = parent
            self.colony = parent.colony
        # self.neighbors = []
        #self.neighbors = self.get_neighbors()
        self.pos = pos

    def connect_with(self, corallite):
        if corallite not in self.connected_neighbor:
            self.connected_neighbor.append(corallite)
            if self not in corallite.connected_neighbor:
                corallite.connected_neighbor.append(self)

    def disconnect_with(self, corallite):
        if corallite in self.connected_neighbor:
            self.connected_neighbor.remove(corallite)
            if self in corallite.connected_neighbor:
                corallite.connected_neighbor.remove(self)

    def get_distance(self, c):
        dist = linalg.norm(self.pos - c.pos)
        return dist

    def get_neighbors(self, log=False):
        neighbor_list = []
        for c in self.colony.corallites:
            if c.id == self.id: continue
            # if c.dead : continue
            dist = self.get_distance(c)
            if log:
                print self.id, self.pos, c.id, c.pos, dist
            if dist < NEIGHBOR_DISTANCE_THRESHOLD:
                neighbor_list.append(c)
        return neighbor_list

    def move(self, vector=array([0, 0, 0])):
        self.pos += vector

    def calculate_growth_vector(self):
        # get neighbors
        # print "grow ", self
        #print self
        neighbors = self.get_neighbors()
        # check distances to neighboring corallites
        self.min_dist = 999
        self.max_dist = -1

        # lateral push
        self.lateral_vector = array([0, 0, 0], float)
        pos_sum = array([0, 0, 0], float)
        pos_avr = array([0, 0, 0], float)
        self.number_of_living_neighbors = 0
        #print "corallite id", self.id, self.pos
        for n in neighbors:
            #print self.id, n.id
            if n.id == self.id: continue
            if n.dead == False:
                self.number_of_living_neighbors += 1
                pos_sum += n.pos
            dist = self.get_distance(n)
            if dist > 0:
                #print self, " to ", n, " ", dist
                if n.dead:
                    self.lateral_vector += ( self.pos - n.pos ) * self.move_ratio_per_tick / ( dist ** self.colony.away_factor_1 )
                else:
                    #print "    neighbor", n.id, n.pos, self.get_distance(n), n.is_neighbor
                    self.min_dist = min(self.min_dist, dist)
                    self.max_dist = max(self.max_dist, dist)
                    self.lateral_vector += ( self.pos - n.pos ) * self.move_ratio_per_tick / ( dist ** self.colony.away_factor_2 )
        if self.number_of_living_neighbors > 0:
            self.pos_avr = pos_sum / self.number_of_living_neighbors
        else:
            self.pos_avr = array([0, 0, 0], float)
            #print "lateral", lateral_vector
            #print "lateral movement:", lateral_vector
        #print "lateral movement final:", lateral_vector

        ''' adjust up vector '''
        self.number_of_neighbors = len(neighbors)
        triangle_list = []
        if self.number_of_living_neighbors > 2:
            for i in range(self.number_of_neighbors - 2):
                for j in range(i + 1, self.number_of_neighbors - 1):
                    for k in range(j + 1, self.number_of_neighbors):
                        if neighbors[i].dead == False and neighbors[j].dead == False and neighbors[k].dead == False:
                            triangle_list.append([i, j, k])
                            #print "triangle", i, j, k
            up_candidate_list = []
            for triangle in triangle_list:
                #print "triangle:", triangle, neighbors[triangle[0]].id,neighbors[triangle[1]].id, neighbors[triangle[2]].id
                v1 = neighbors[triangle[0]].pos - neighbors[triangle[1]].pos
                v2 = neighbors[triangle[1]].pos - neighbors[triangle[2]].pos
                #print "v1, v2", v1, v2
                v_up = array([v1[0] * v2[1] - v1[1] * v2[0], v1[1] * v2[2] - v1[2] * v2[1], v1[2] * v2[0] - v1[0] * v2[2]],
                             float)
                ip = dot(v_up, self.upwardVector)
                #print "vup", v_up, "upward", self.upwardVector, "ip:", ip
                if ( ip < 0 ):
                    v_up = array([v2[0] * v1[1] - v2[1] * v1[0], v2[1] * v1[2] - v2[2] * v1[1], v2[2] * v1[0] - v2[0] * v1[2]],
                                 float)
                len_v_up = linalg.norm(v_up)
                if len_v_up > 0:
                    v_up = v_up / linalg.norm(v_up)
                    up_candidate_list.append(v_up)
            sum_up = array([0, 0, 0], float)
            for v in up_candidate_list:
                #print "up_candidate", v
                sum_up += v
            v_up = sum_up / len(up_candidate_list)
            self.upwardVector = v_up * self.move_ratio_per_tick
            #print "up", self.upwardVector
            self.upwardVector += array([0.0, 0.0, 1.0], float) * self.move_ratio_per_tick
            #print "up", self.upwardVector
        else:
            self.upwardVector = array([0.0, 0.0, 1.0], float) * self.move_ratio_per_tick

        if self.colony.enhance_vertical_growth:
            verticalVector = array([0.0, 0.0, 1.0], float)
            cosine_theta = dot(self.upwardVector, verticalVector) / linalg.norm(self.upwardVector) * linalg.norm(
                verticalVector)
            print "    cos theta", cosine_theta
            theta = math.acos(cosine_theta)
            print "    theta", theta
            self.upwardVector += verticalVector * cosine_theta * self.move_ratio_per_tick * 0.2

            #self.upwardVector = array( [ 0.0, 0.0, 0.0 ], float)
            #pass
            #print "up", self.upwardVector
            #self
            #self.upwardVector = array( [ 0.0, 0.0, 0.0 ], float)  * self.move_ratio_per_tick
        print self.id, "upward vector:", self.upwardVector,
        print "lateral vector:", self.lateral_vector
        self.move_vector = array([0, 0, 0], float)
        self.move_vector += self.upwardVector
        self.move_vector += self.lateral_vector

        # divide if too far away from neighbors
        # if min_dist > NEIGHBOR_DISTANCE_THRESHOLD:

    def reproduce(self):
        if self.number_of_living_neighbors < self.colony.neighbor_count_threshold and self.min_dist > self.colony.min_distance_for_division:
            child = Corallite(self)
            child.upwardVector = array(self.upwardVector[:])
            child.pos = array(self.pos[:])
            if False:
                move_vector = self.lateral_vector
                lateral_vector = array([0, 0, 0], float)
            else:
                move_vector = child.pos - self.pos_avr
                len_move_vec = linalg.norm(move_vector)
                if len_move_vec > 0:
                    move_vector = move_vector * self.move_ratio_per_tick / ( len_move_vec ** self.colony.away_factor_2 )
                    move_vector += array([self.get_random_factor(), self.get_random_factor(), self.get_random_factor()],
                                         float) * self.move_ratio_per_tick
            child.move(move_vector)
            child.move_vector = self.move_vector
            child.selected = self.selected
            self.colony.add_corallite(child)
            # print self.id, self.pos, "divide", min_dist, number_of_living_neighbors, child.id, child.pos
            #print child.id
            #print child


            # calculate upVector

            #print self.move_vector
            #self.move_vector += array( [0,0,0.1], float)

    def elongate(self):

        if self.min_dist < self.colony.min_distance_for_division:
            return
        # if len( self.connected_neighbor ) == 0:
        #    return

        child = Corallite(self)
        child.upwardVector = array(self.upwardVector[:])

        neighbor = self.connected_neighbor[0]
        child.pos = array(( self.pos[:] + neighbor.pos[:] ) / 2.0)
        self.disconnect_with(neighbor)
        self.connect_with(child)
        neighbor.connect_with(child)

        move_vector = array([self.get_random_factor(), self.get_random_factor(), self.get_random_factor()],
                            float) * self.move_ratio_per_tick
        child.move(move_vector)
        child.selected = self.selected
        self.colony.add_corallite(child)
        new_edge_1 = [self.id, child.id]
        new_edge_2 = [neighbor.id, child.id]
        old_edge = [neighbor.id, self.id]
        new_edge_1.sort()
        new_edge_2.sort()
        old_edge.sort()

        if random.random() > 0.1:
            self.colony.edges.append(new_edge_1)
        self.colony.edges.append(new_edge_2)
        if old_edge in self.colony.edges:
            self.colony.edges.remove(old_edge)


        #print self.pos
        """ add another divide condition (boundary && tick?) """
        # to divide or not to divide, that is the question

        # get normal vector

        # add random factor

        # move along normal vector

    def branch(self):

        if self.min_dist < self.colony.min_distance_for_division:
            return
        if len(self.connected_neighbor) != 2:
            return

        child = Corallite(self)
        child.upwardVector = array(self.upwardVector[:])

        neighbor = self.connected_neighbor[0]
        child.pos = array(
            self.pos[:] + self.pos[:] - ( self.connected_neighbor[0].pos[:] + self.connected_neighbor[1].pos[:] ) / 2.0)
        self.connect_with(child)

        move_vector = array([self.get_random_factor(), self.get_random_factor(), self.get_random_factor()],
                            float) * self.move_ratio_per_tick
        child.move(move_vector)
        child.selected = self.selected
        self.colony.add_corallite(child)
        new_edge = [self.id, child.id]
        new_edge.sort()
        self.colony.edges.append(new_edge)

        # print self.pos
        """ add another divide condition (boundary && tick?) """
        # to divide or not to divide, that is the question

        # get normal vector

        # add random factor

        # move along normal vector


    def grow(self):
        # print self.id, "grow from pos:", self.pos, "move:", self.move_vector
        if self.trace == None:
            self.trace = Corallite(self.colony)
            self.trace.pos = array(self.pos[:])
            self.trace.dead = True
            self.trace.deadcount = 10
        if self.pos[2] + self.move_vector[2] < 0:
            #print self.move_vector,
            hv = array([0, 0, 0], float)
            hv[0:3] = self.move_vector[0:3]
            #print hv,
            hv[2] = 0
            #print hv,
            len1 = linalg.norm(self.move_vector)
            len2 = linalg.norm(hv)
            #print len1, len2,
            hv = hv * ( len1 / len2 )
            self.move_vector = hv
            #print self.move_vector
        self.pos += self.move_vector
        self.move_vector = array([0, 0, 0], float)
        self.trace.deadcount -= 1
        if self.trace.deadcount == 0:
            self.colony.add_corallite(self.trace)
            self.trace = None


    def get_random_factor(self):
        f = 0.5 - random.random()
        # print "random:", f
        return f

    def __str__(self):
        if self.dead == False:
            return "[" + str(self.id) + "] (" + str(self.pos[0]) + "," + str(self.pos[1]) + "," + str(self.pos[2]) + ")"
        return ""


class CoralColony():
    def __init__(self):
        self.corallites = []
        self.edges = []
        self.faces = []
        self.last_id = 0
        self.time = 0
        self.className = "Colony"
        self.enhance_vertical_growth = False
        """ initial corallites """
        self.elongate = True
        self.add_corallite(Corallite(self, -1, array([1, 0, 0], float)))
        # self.add_corallite( Corallite( self, -1, array( [  0,  1, 0 ], float ) ) )
        #self.add_corallite( Corallite( self, -1, array( [ -1,  0, 0 ], float ) ) )
        #self.add_corallite( Corallite( self, -1, array( [  0, -1, 0 ], float ) ) )
        #self.add_corallite( Corallite( self, -1, array( [  1,  0, 0.5 ], float ) ) )
        #self.add_corallite( Corallite( self, -1, array( [  0,  1, 0.5 ], float ) ) )
        #self.add_corallite( Corallite( self, -1, array( [ -1,  0, 0.5 ], float ) ) )
        #self.add_corallite( Corallite( self, -1, array( [  0, -1, 0.5 ], float ) ) )
        #self.add_connection( 0, 1 )
        #self.add_connection( 1, 3 )
        #self.add_connection( 2, 3 )
        #self.add_connection( 3, 4 )
        #self.edges.append( [ 1, 2 ] )
        #self.edges.append( [ 2, 4 ] )
        #self.edges.append( [ 3, 4 ] )
        #self.edges.append( [ 4, 5 ] )
        ##self.add_connection( 4, 5 )
        #self.add_connection( 5, 6 )
        #self.add_connection( 6, 7 )
        #self.edges.append( [ 5, 6 ] )
        #self.edges.append( [ 6, 7 ] )
        #self.edges.append( [ 7, 8 ] )
        #self.add_face( [ 1, 2, 3 ] )
        #self.add_face( [ 1, 3, 4 ] )

        #self.add_corallite( Corallite( self, -1, array( [  0,  0, 0 ], float ) ) )
        #self.add_corallite( Corallite( self, -1, array( [  0,  0, 0.5 ], float ) ) )

        self.reproduction_rate = 1.0
        self.elongation_rate = 1.0
        self.branching_rate = 1.0
        """for i in range(-2,2):
            for j in range(-2,2):
                c = Corallite( self, -1, array( [ i, j, -1], float ) )
                c.dead = True
                self.add_corallite( c )
        """

    def add_connection(self, idx1, idx2):
        self.corallites[idx1].connect_with(self.corallites[idx2])

    def add_face(self, face):
        self.faces.append(face)

    def set_reproduction_rate(self, rate):
        self.reproduction_rate = rate

    def set_elongation_rate(self, rate):
        self.elongation_rate = rate

    def set_branching_rate(self, rate):
        self.branching_rate = rate

    def set_neighbor_distance_threshold(self, dist):
        self.neighbor_distance_threshold = dist

    def set_neighbor_count_threshold(self, count):
        self.neighbor_count_threshold = count

    def set_minimum_distance_for_division(self, dist):
        self.min_distance_for_division = dist

    def set_away_1(self, away):
        self.away_factor_1 = away

    def set_away_2(self, away):
        self.away_factor_2 = away

    def rotate_3d(self, theta, axis):
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        r_mx = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        if ( axis == 'Z' ):
            r_mx[0][0] = cos_theta
            r_mx[0][1] = sin_theta
            r_mx[1][0] = -1 * sin_theta
            r_mx[1][1] = cos_theta
        elif ( axis == 'Y' ):
            r_mx[0][0] = cos_theta
            r_mx[0][2] = sin_theta
            r_mx[2][0] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        elif ( axis == 'X' ):
            r_mx[1][1] = cos_theta
            r_mx[1][2] = sin_theta
            r_mx[2][1] = -1 * sin_theta
            r_mx[2][2] = cos_theta
        # print "rotation matrix", r_mx

        for c in ( self.corallites ):
            x_rotated = c.pos[0] * r_mx[0][0] + c.pos[1] * r_mx[1][0] + c.pos[2] * r_mx[2][0]
            y_rotated = c.pos[0] * r_mx[0][1] + c.pos[1] * r_mx[1][1] + c.pos[2] * r_mx[2][1]
            z_rotated = c.pos[0] * r_mx[0][2] + c.pos[1] * r_mx[1][2] + c.pos[2] * r_mx[2][2]
            c.pos[0] = x_rotated
            c.pos[1] = y_rotated
            c.pos[2] = z_rotated

    def grow(self):
        # if self.time == 100: return
        #print "colony grow", self.time, len( self.corallites )
        self.time += 1
        c_dead = 0
        c_alive = 0
        for c in self.corallites:
            if c.dead == False:
                c_alive += 1
                c.calculate_growth_vector()
                rnd = random.random()
                print "self.time:", self.time, "rnd", rnd, "rep rate", self.reproduction_rate
                if rnd < self.reproduction_rate:
                    c.reproduce()

                    #rnd = random.random()
                    #if rnd < self.elongation_rate :
                    #    print "elongation", rnd, self.elongation_rate
                    #    c.elongate()

                    #rnd = random.random()
                    #if rnd < self.branching_rate :
                    #    c.branch()

            else:
                c_dead += 1
        for c in self.corallites:
            if c.dead == False:
                c.grow()
        print "\t".join(["%s" % k for k in ( self.time, len(self.corallites), c_alive, c_dead )])
        # for c in self.corallites:
        #   print c

    def add_corallite(self, c):
        self.last_id += 1
        c.id = self.last_id
        # if c.id == 10:
        #  c.selected = True
        self.corallites.append(c)


ID_CORALLITE_LISTCTRL = 1001
ID_NEIGHBOR_LISTCTRL = 1002
ID_CHK_SHOW_INDEX = 1003
ID_CHK_ENHANCE_VERTICAL_GROWTH = 1004


class CoralMakerFrame(wx.Frame):
    def __init__(self, parent, id, name):
        wx.Frame.__init__(self, parent, id, name, wx.DefaultPosition, wx.Size(1024, 768))

        self.colony = CoralColony()
        self.interval = 100
        self.growth_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.growth_timer)
        self.growth_timer.Start(self.interval)
        self.show_index = False
        self.enhance_vertical_growth = False
        # self.is_growing = True

        self.control = MdCanvas(self)
        self.control.SetMinSize((800, 600))
        self.Button1 = wx.Button(self, wx.ID_ANY, 'Play')
        self.Button2 = wx.Button(self, wx.ID_ANY, 'Reset')
        self.LoadNeighborButton = wx.Button(self, wx.ID_ANY, 'Watch')
        self.ButtonExport = wx.Button(self, wx.ID_ANY, 'Export')
        lb1 = wx.StaticText(self, wx.ID_ANY, '')
        lb2 = wx.StaticText(self, wx.ID_ANY, '')

        self.chkShowIndex = wx.CheckBox(self, ID_CHK_SHOW_INDEX, "Show Index")
        self.Bind(wx.EVT_CHECKBOX, self.ToggleShowIndex, id=ID_CHK_SHOW_INDEX)
        self.chkShowIndex.SetValue(self.show_index)
        self.chkEnhanceVerticalGrowth = wx.CheckBox(self, ID_CHK_ENHANCE_VERTICAL_GROWTH, "Enhance Vert. Growth")
        self.Bind(wx.EVT_CHECKBOX, self.ToggleEnhanceVerticalGrowth, id=ID_CHK_ENHANCE_VERTICAL_GROWTH)
        self.chkEnhanceVerticalGrowth.SetValue(self.show_index)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(self.Button1, wx.ALIGN_CENTER)
        sizer1.Add(self.Button2, wx.ALIGN_CENTER)
        sizer1.Add(self.ButtonExport, wx.ALIGN_CENTER)

        self.forms = dict()

        self.neighborDistanceLabel = wx.StaticText(self, -1, 'Neigh. Dist', style=wx.ALIGN_RIGHT)
        self.forms['neighbor_distance'] = wx.TextCtrl(self, -1, str(NEIGHBOR_DISTANCE_THRESHOLD))
        self.neighborCountLabel = wx.StaticText(self, -1, 'No. Neighbor', style=wx.ALIGN_RIGHT)
        self.forms['neighbor_count'] = wx.TextCtrl(self, -1, str(NEIGHBOR_COUNT_THRESHOLD))
        self.minDistLabel = wx.StaticText(self, -1, 'Min. Dist', style=wx.ALIGN_RIGHT)
        self.forms['minimum_distance'] = wx.TextCtrl(self, -1, str(MIN_DISTANCE_FOR_DIVISION))
        self.reproductionLabel = wx.StaticText(self, -1, 'Reproduction rate', style=wx.ALIGN_RIGHT)
        self.forms['reproduction'] = wx.TextCtrl(self, -1, str(REPRODUCTION_RATE))
        self.elongationLabel = wx.StaticText(self, -1, 'Elongation rate', style=wx.ALIGN_RIGHT)
        self.forms['elongation'] = wx.TextCtrl(self, -1, str(ELONGATION_RATE))
        self.branchingLabel = wx.StaticText(self, -1, 'Branchingrate', style=wx.ALIGN_RIGHT)
        self.forms['branching'] = wx.TextCtrl(self, -1, str(BRANCHING_RATE))
        self.away1Label = wx.StaticText(self, -1, 'Away 1', style=wx.ALIGN_RIGHT)
        self.forms['away1'] = wx.TextCtrl(self, -1, str(AWAY_1))
        self.away2Label = wx.StaticText(self, -1, 'Away 2', style=wx.ALIGN_RIGHT)
        self.forms['away2'] = wx.TextCtrl(self, -1, str(AWAY_2))
        self.coralliteListLabel = wx.StaticText(self, -1, 'Corallite', style=wx.ALIGN_RIGHT)
        #self.coralliteListButton = wx.Button(self, -1, 'Load list' )
        self.coralliteList = wx.ListBox(self, ID_CORALLITE_LISTCTRL, choices=(), size=(100, 200), style=wx.LB_SINGLE)
        self.neighborListLabel = wx.StaticText(self, -1, 'Neighbor', style=wx.ALIGN_RIGHT)
        #self.coralliteListButton = wx.Button(self, -1, 'Load list' )
        self.neighborList = wx.ListBox(self, ID_NEIGHBOR_LISTCTRL, choices=(), size=(100, 200), style=wx.LB_EXTENDED)

        sizer2 = wx.FlexGridSizer(3, 3, 0, 0)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.chkShowIndex, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.chkEnhanceVerticalGrowth, flag=wx.EXPAND)
        sizer2.Add(self.neighborDistanceLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['neighbor_distance'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.neighborCountLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['neighbor_count'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.minDistLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['minimum_distance'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.reproductionLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['reproduction'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.elongationLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['elongation'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.branchingLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['branching'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.away1Label, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['away1'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.away2Label, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.forms['away2'], flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.coralliteListLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.coralliteList, flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.LoadNeighborButton, flag=wx.EXPAND | wx.ALIGN_CENTER)
        sizer2.Add(self.neighborListLabel, flag=wx.EXPAND)
        sizer2.Add((10, 10), flag=wx.EXPAND)
        sizer2.Add(self.neighborList, flag=wx.EXPAND | wx.ALIGN_CENTER)

        fs = wx.FlexGridSizer(2, 2, 10, 5)
        fs.AddGrowableCol(0)
        fs.AddGrowableCol(1)
        fs.AddGrowableRow(0)
        fs.Add(self.control, 0, wx.EXPAND)
        fs.Add(sizer2, 0, wx.ALIGN_CENTER)
        fs.Add(sizer1, 0, wx.EXPAND)
        fs.Add(lb2, 0, wx.ALIGN_CENTER)
        self.Bind(wx.EVT_BUTTON, self.OnButton1, self.Button1)
        self.Bind(wx.EVT_BUTTON, self.OnButton2, self.Button2)
        self.Bind(wx.EVT_BUTTON, self.OnLoadNeighbor, self.LoadNeighborButton)
        self.Bind(wx.EVT_BUTTON, self.OnExport, self.ButtonExport)
        #self.Bind( wx.EVT_BUTTON, self.OnLoadList, self.coralliteListButton )
        self.Bind(wx.EVT_LISTBOX, self.OnCoralliteSelected, id=ID_CORALLITE_LISTCTRL)
        self.SetSizer(fs)
        self.init_control = False
        self.is_growing = False
        self.is_watching_corallite = False

        self.ResetColony()
        #self.control.SetColony( self.colony )
        # self.control.ShowIndex()
        self.control.BeginAutoRotate(500)

    def ToggleShowIndex(self, event):
        self.show_index = self.chkShowIndex.GetValue()
        # print self.show_index
        if ( self.show_index ):
            self.control.ShowIndex()
        else:
            self.control.HideIndex()

    def ToggleEnhanceVerticalGrowth(self, event):
        self.enhance_vertical_growth = self.chkEnhanceVerticalGrowth.GetValue()
        self.colony.enhance_vertical_growth = self.enhance_vertical_growth

    def OnExport(self, event):
        result_str = ""
        actual_str = ""
        l_count = 0
        result_str += "3\n"
        # result_str += str( len( self.colony.corallites) )
        print "count:", l_count
        living_corallites = []
        for c in self.colony.corallites:
            if c.dead == False:
                living_corallites.append(c)
                actual_str += str(c.pos[0]) + "\t" + str(c.pos[1]) + "\t" + str(c.pos[2]) + "\n"
                l_count += 1
                print "count:", l_count
        result_str += str(l_count) + "\n"
        result_str += actual_str
        filename = "colony.dat"
        fh = file(filename, 'w')
        fh.write(result_str)
        fh.close()

        import os

        os.system('"qdelaunay Qt s i TO output.dat < colony.dat"')

        f = open("output.dat", 'r')
        data = f.read()
        f.close()
        lines = [l.strip() for l in data.split("\n")]
        header = lines[0]
        lines = lines[1:]
        triangles = []
        dup_triangles = []
        for line in lines:
            if line == '': continue
            thed = map(int, line.split(" "))
            thed = map(lambda x: living_corallites[x].id, thed)
            print thed
            thed.sort()
            for i in range(len(thed)):
                t = thed[:]
                t.remove(t[i])
                if not t in triangles and not t in dup_triangles:
                    triangles.append(t)
                    print "\t", t
                else:
                    triangles.remove(t)
                    dup_triangles.append(t)
                    print "\t", t, "duplicate!"
        triangles.sort()
        print len(triangles)
        print triangles
        """    """
        edges = []
        for tr in triangles:
            for i in range(len(tr)):
                e = tr[:]
                e.remove(e[i])
                if e in edges:
                    print "\t", e, "duplicate!"
                else:
                    #if self.colony.corallites[e[0]-1].get_distance(self.colony.corallites[e[1]-1] ) < 2 * float( self.forms['minimum_distance'].GetValue() ) :
                    edges.append(e)
                    print "\t", e
        edges.sort()
        print len(edges), edges
        """    """
        self.colony.edges = edges
        return


    def OnCoralliteSelected(self, event):
        print "on select"
        selected_list = self.coralliteList.GetSelections()
        print selected_list
        for c in self.colony.corallites:
            c.selected = False
        for c in selected_list:
            self.coralliteList.GetClientData(c).selected = True
            # pass
            #c.selected = True
        return

    def OnLoadList(self, event):
        self.Button1.SetLabel("Play")
        self.is_growing = False
        self.LoadList()

    def OnLoadNeighbor(self, event):
        idx = self.coralliteList.GetSelections()
        print "load neighbor selection", idx
        c = self.coralliteList.GetClientData(idx[0])
        print "watch colrallite", c.id
        self.WatchCorallite(c)

    def WatchCorallite(self, corallite):
        if self.is_watching_corallite == True:
            self.corallite_being_watched.being_watched = False
            for c in self.colony.corallites:
                c.being_watched = False
                c.is_neighbor = False
        self.is_watching_corallite = True
        self.corallite_being_watched = corallite

        corallite.being_watched = True
        self.UpdateNeighborList(corallite)

    def UpdateNeighborList(self, corallite):
        for c in self.colony.corallites:
            c.is_neighbor = False
        self.neighborList.Clear()
        neighbors = corallite.get_neighbors()  # log = True)
        # print corallite.id, corallite.pos
        for n in neighbors:
            if n.dead == False:
                n.is_neighbor = True
                self.neighborList.Append(str(n.id), n)
                #print "  neighbor", n.id, n.is_neighbor, n.pos

    def LoadList(self):
        selected_list = self.coralliteList.GetSelections()
        self.coralliteList.Clear()
        for c in self.colony.corallites:
            if c.dead == False:
                lastidx = self.coralliteList.Append(str(c.id), c)
                if c.selected == True:
                    self.coralliteList.SetSelection(lastidx)
        for idx in selected_list:
            self.coralliteList.SetSelection(idx)

    def OnButton1(self, event):
        if self.is_growing:
            self.is_growing = False
            self.Button1.SetLabel("Play")
        else:
            self.is_growing = True
            self.Button1.SetLabel("Pause")

    def OnButton2(self, event):

        self.ResetColony()

    def ResetColony(self):
        self.colony = CoralColony()
        self.colony.set_minimum_distance_for_division(float(self.forms['minimum_distance'].GetValue()))
        self.colony.set_neighbor_distance_threshold(float(self.forms['neighbor_distance'].GetValue()))
        self.colony.set_neighbor_count_threshold(float(self.forms['neighbor_count'].GetValue()))
        self.colony.set_reproduction_rate(float(self.forms['reproduction'].GetValue()))
        self.colony.set_elongation_rate(float(self.forms['elongation'].GetValue()))
        self.colony.set_branching_rate(float(self.forms['branching'].GetValue()))
        self.colony.set_away_1(float(self.forms['away1'].GetValue()))
        self.colony.set_away_2(float(self.forms['away2'].GetValue()))
        self.control.SetColony(self.colony)

    def OnTimer(self, event):
        if self.is_growing:
            self.colony.grow()
            self.LoadList()
            if self.is_watching_corallite == True:
                self.UpdateNeighborList(self.corallite_being_watched)


class CoralMakerApp(wx.App):
    def OnInit(self):
        # self.dbpath = ""
        self.frame = ''
        self.frame = CoralMakerFrame(None, -1, 'CoralMaker')
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True


app = CoralMakerApp(0)
#print sys.argv[0]
app.MainLoop()
