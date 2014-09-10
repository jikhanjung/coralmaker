#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Mar 9, 2014

@author: jikhanjung
'''

import wx
from CoralConfig2D import *
from numpy import *


class CoralColony():
	def __init__(self, depth=1):
		self.className = "CoralColony"
		self.depth = depth
		self.polyp_list = []
		self.last_id = 0
		self.month = 0
		self.prev_polyp_count = 0
		self.lateral_growth_criterion = 0.01
		self.lateral_growth_period = 1  #month
		self.annual_shape = []
		self.space = zeros(( MAX_COLONY_SIZE, MAX_COLONY_SIZE))
		self.occupied_space = []
		self.apical_polyp_list = []
		self.config = {}
		return

	def add_polyp(self, p):
		self.last_id += 1
		p.id = self.last_id
		p.prev_pos[:] = p.pos[:]
		self.polyp_list.append(p)
		return

	def lateral_growth_check(self):
		polyp_count = len(self.polyp_list)
		#print "polyp_count:", self.prev_polyp_count, polyp_count
		if self.config['peripheral_budding'] == ID_NONE:
			return
		if (float(polyp_count - self.prev_polyp_count) / float(self.prev_polyp_count) < self.config[
			'lateral_growth_criterion'] ):
			self.head_polyp.grow_laterally()
			self.tail_polyp.grow_laterally()
			#pass
		self.prev_polyp_count = polyp_count

	def record_annual_growth(self):
		p = self.head_polyp
		arr = []
		pt = [p.pos[X_INDEX], p.pos[Z_INDEX] * -1]
		arr.append(pt)
		while p.next_polyp:
			p = p.next_polyp
			#p.record_position()
			pt = [p.pos[X_INDEX], p.pos[Z_INDEX] * -1]
			arr.append(pt)
		self.annual_shape.append(arr)

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
					if p.has_enough_space_2d(p.next_polyp):
						p.bud_2d(p.next_polyp)

		for p in self.polyp_list:
			if p.alive:
				p.calculate_new_growth_vector()

		for p in self.polyp_list:
			if p.alive:
				p.apply_new_growth_vector()

		for p in self.polyp_list:
			if p.alive:
				p.check_dead_or_alive()

		if len(self.apical_polyp_list) > 0:
			print "apical polyp!"
			for p in self.polyp_list:
				if p.alive and p.apical_polyp == False:
					min_dist = p.radius * 20
					for ap in self.apical_polyp_list:
						dist = p.get_distance(ap)
						if dist < min_dist:
							min_dist = dist

					if min_dist == p.radius * 20:
						p.apical_polyp = True
						self.apical_polyp_list.append(p)

						#for p in self.polyp_list:
						#print p.id,
		#print

		return

	def init_colony_2d(self):
		for i in range(len(self.polyp_list) - 1):
			self.polyp_list[i].next_polyp = self.polyp_list[i + 1]
			self.polyp_list[i + 1].prev_polyp = self.polyp_list[i]
		#for p in self.polyp_list:
		#    p.prev_pos = p.pos
		self.head_polyp = self.polyp_list[0]
		self.tail_polyp = self.polyp_list[len(self.polyp_list) - 1]
		self.prev_polyp_count = len(self.polyp_list)

	def to_string(self):
		ret_str = ""
		p = self.head_polyp
		ret_str += p.to_string()
		while p.next_polyp:
			p = p.next_polyp
			ret_str += p.to_string()
		return ret_str

	def print_to_image(self, img):
		(w, h) = img.size
		origin = [w / 2, h - 10]
		#print "num polyps", len( self.polyp_list )
		for p in self.polyp_list:
			color = "red"
			if p == self.head_polyp or p == self.tail_polyp:
				color = "black"
			p.print_to_image(img, origin, color)
			#print p.pos

	def print_to_dc(self, dc, origin):
		w, h = dc.GetSize()
		#print "dc size", w, h
		#origin = [ w / 2, h - 10 ]
		for shape in self.annual_shape:
			zoomed_shape = []
			for pt in shape:
				x = pt[0]
				y = pt[1]
				zoomed_shape.append(wx.Point(x * self.config['zoom'], y * self.config['zoom']))
			dc.DrawLines(zoomed_shape, xoffset=origin[0], yoffset=origin[1])
		#print "num polyps", len( self.polyp_list )
		for p in self.polyp_list:
			color = "red"
			if p == self.head_polyp or p == self.tail_polyp:
				color = "black"
			p.print_to_dc(dc, origin, color)

		if self.config['show_skeleton']:
			for p in self.occupied_space:
				dc.SetPen(wx.Pen("yellow", 1))
				dc.DrawPoint(p[0] * self.config['zoom'] + origin[0], -1 * p[1] * self.config['zoom'] + origin[1])
