#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Mar 9, 2014

@author: jikhanjung
'''
# import os
import wx
#import sys
#import random
import math
from numpy import array, linalg, dot, matrix, cross, squeeze, asarray
#from opengltest import MdCanvas
import ImageDraw
import CoralConfig3D as ccfg


class CoralPolyp():
	def __init__(self, parent, pid=-1, pos=array([0, 0, 0], float), radius=ccfg.POLYP_RADIUS, height=1):
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
		self.prev_pos = array([0, 0, 0], float)
		self.pos_list = []
		self.prev_polyp = None
		self.next_polyp = None
		self.age_in_month = 0
		self.selected = False
		self.irradiance = -1
		self.growth_rate = -1
		self.alive = True
		self.next_distance = 99
		self.prev_distance = 99
		self.apical_polyp = False
		self.dead = False
		self.is_neighbor = False
		if ( parent.className == "CoralColony" ):
			self.colony = parent
		else:
			self.colony = parent.colony

	def record_position(self):
		curr_pos = []
		curr_pos[:] = self.pos[:]
		self.pos_list.append(curr_pos)
		#print "record annual polyp position", self.id, curr_pos, self.annual_pos_list
		return self.pos

	def scan_neighbors(self):
		polyp_list = self.colony.polyp_list
		for polyp in polyp_list:
			if polyp.id == self.id:
				pass
			dist = self.get_distance(polyp)
			if dist >= ccfg.NEIGHBOR_DISTANCE_MULTIPLIER * self.radius:
				pass
			else:
				self.neighbor_list.append(polyp)

	def get_distance(self, c):
		dist = linalg.norm(self.pos - c.pos)
		return dist

	def get_depth(self):
		return self.colony.depth

	def _get_irradiance(self):
		depth = self.get_depth()
		vec = self.grow_vector / linalg.norm(self.grow_vector)
		cos_val = vec[ccfg.Z_INDEX]
		#print cos_val

		radiance_base = self.config['surface_irradiance'] * math.exp(
			-1 * self.config['attenuation_coefficient'] * depth)  #Wm-2

		floor_reflection = radiance_base * self.config['reflection_rate']
		direct_irradiance = radiance_base * cos_val

		total_irradiance = floor_reflection + direct_irradiance

		if total_irradiance > self.config['max_irradiance']:
			return 1
		else:
			return total_irradiance / self.config['max_irradiance']

		return 1

	def get_irradiance(self):
		depth = self.get_depth()
		depth = depth - self.pos[ccfg.Z_INDEX] / 100
		vec = self.growth_vector / linalg.norm(self.growth_vector)
		#cos_val = max( vec[ccfg.Z_INDEX], 0 )

		cos_val = ( ( vec[ccfg.Z_INDEX] + 1.0 ) / 2.0 ) ** 2

		radiance_base = self.colony.config['surface_irradiance'] * math.exp(
			-1 * self.colony.config['attenuation_coefficient'] * depth)  #Wm-2

		#floor_reflection = radiance_base * self.colony.config['reflection_rate']
		floor_reflection = 0
		direct_irradiance = radiance_base * cos_val

		total_irradiance = floor_reflection + direct_irradiance
		self.irradiance = min(total_irradiance, self.colony.config['max_irradiance']) / self.colony.config['max_irradiance']
		return self.irradiance

		if total_irradiance > self.colony.config['max_irradiance']:
			return 1
		else:
			return total_irradiance / self.colony.config['max_irradiance']

		return 1

	def grow(self):
		irradiance = self.get_irradiance()
		growth_rate = 1 - math.exp(-1.0 * irradiance * self.colony.config['growth_constant'])

		if self.colony.config['determinate_growth'] == True and self.apical_polyp == False:
			growth_rate = growth_rate * math.exp(-1.0 * ( self.age_in_month / 12 ))
		self.growth_rate = growth_rate
		self.pos += ( self.growth_vector / linalg.norm(self.growth_vector) ) * growth_rate
		self.age_in_month += 1
		#print self.id, self.pos
		return

	def check_space(self):
		#return
		if self.next_polyp:
			p_list = [self.pos, self.next_polyp.pos]
			for pos_list in [self.pos_list, self.next_polyp.pos_list]:
				if len(pos_list) > 0:
					p_list.append(pos_list[-1])
			v1 = p_list[1] - p_list[0]

			x_list = [p[ccfg.X_INDEX] for p in p_list]
			z_list = [p[ccfg.Z_INDEX] for p in p_list]

			min_x = min(x_list)
			max_x = max(x_list)
			min_z = min(z_list)
			max_z = max(z_list)

			from_x = int(math.ceil(min_x))
			to_x = int(math.floor(max_x))
			if from_x > to_x:
				temp_x = from_x
				from_x = to_x
				to_x = temp_x
			from_z = int(math.ceil(min_z))
			to_z = int(math.floor(max_z))
			if from_z > to_z:
				temp_z = from_z
				from_z = to_z
				to_z = temp_z
			#origin_x = int( ccfg.MAX_COLONY_SIZE / 2 )
			ANGLE_THRESHOLD = ( math.pi / 45 )
			if self.selected:
				print p_list
				print from_x, to_x, from_z, to_z
			for x in range(from_x, to_x + 1):
				for z in range(from_z, to_z + 1):
					p3 = array([x, 0, z], float)
					vec = p3 - p_list[0]
					angle = self.get_angle_between_vectors(v1, vec)
					if self.selected: print x, z, angle, ANGLE_THRESHOLD
					if angle > 0:  #math.fabs( angle ) < ANGLE_THRESHOLD:
						self.colony.occupied_space.append([x, z])  #space[origin_x + x,z] = 1
						#if self.selected: print "yes", x, z


	def die(self):
		#print "die", self.id
		self.alive = False
		self.dead = True
		if self.next_polyp:
			if self.prev_polyp:
				self.next_polyp.prev_polyp = self.prev_polyp
				self.prev_polyp.next_polyp = self.next_polyp
				self.next_polyp = None
				self.prev_polyp = None
			else:
				self.next_polyp.prev_polyp = None
				self.colony.head_polyp = self.next_polyp
				self.next_polyp = None
		else:
			if self.prev_polyp:
				self.prev_polyp.next_polyp = None
				self.colony.tail_polyp = self.prev_polyp
				self.prev_polyp = None
		return

	def check_dead_or_alive(self):
		#print "check die"
		if self.pos[ccfg.Z_INDEX] <= 0 and self.growth_vector[ccfg.Z_INDEX] < 0:
			print self.id, self.pos, self.growth_vector
			self.die()

		if self.next_polyp:
			next_distance = linalg.norm(self.pos - self.next_polyp.pos)
			if next_distance < self.next_distance:
				if next_distance < 0.5:
					self.die()
				else:
					self.next_distance = next_distance

		if self.prev_polyp:
			prev_distance = linalg.norm(self.pos - self.prev_polyp.pos)
			if prev_distance < self.prev_distance:
				if prev_distance < 0.5:
					self.die()
				else:
					self.prev_distance = prev_distance


	def has_enough_space_2d(self, neighboring_polyp):
		dist = self.get_distance(neighboring_polyp)
		if dist > self.radius * 2:
			return True
		return False

	'''
	def find_bud_loc_2d_new(self, neighboring_polyp):
			v1 = self.growth_vector
			v2 = neighboring_polyp.growth_vector

			theta = self.get_angle_between_growth_vectors( v1, v2 )
			#print "theta:", theta


			cos_theta = dot( v1, v2 ) / ( linalg.norm( v1 ) * linalg.norm( v2 ) )#p1.
			theta = math.acos( cos_theta )
			new_growth_vector = self.rotate( v1, theta )
	'''

	def rotate(self, vec, theta):
		#rotation_matrix = matrix( [ [ math.cos( theta ), 0, math.sin( theta )] , [-1 * math.sin(theta ), 1, math.cos(theta) ], [ 0, 0, 1 ]])
		rotation_matrix = matrix([[math.cos(theta), 0, math.sin(theta)],
		                          [0, 1, 0],
		                          [-1 * math.sin(theta), 0, math.cos(theta)],
		])

		new_vec = dot(vec, rotation_matrix)
		vec = squeeze(asarray(new_vec[0]))
		return vec

	def get_angle_between_vectors(self, v1, v2):

		cross_product = cross(v1, v2)
		sin_theta = cross_product[ccfg.Y_INDEX] / ( linalg.norm(v1) * linalg.norm(v2) )

		#if sin_theta > 0:
		#print "plus"
		#else:
		#print "minus"
		theta = math.asin(sin_theta)
		return theta


	def find_bud_loc_2d(self, neighboring_polyp):

		p1 = self.pos
		p2 = neighboring_polyp.pos

		center = self.get_local_center(neighboring_polyp)
		#print p1, p2, "center:", center
		#radius = linalg.norm( p1 - center )
		vec_len = ( linalg.norm(p1 - center) + linalg.norm(p2 - center) ) / 2
		vec = ( ( p1 - center ) / linalg.norm(p1 - center) + ( p2 - center ) / linalg.norm(p1 - center) ) / 2
		new_loc = center + ( vec / linalg.norm(vec) ) * vec_len
		vec /= linalg.norm(vec)
		#print p1, p2, new_loc #"center:", center, "new:", new_loc
		return new_loc, vec

	def bud_2d(self, neighboring_polyp):

		p = CoralPolyp(self)
		p.growth_vector = ( self.growth_vector + neighboring_polyp.growth_vector ) / 2.0
		#p.pos = ( self.pos + neighboring_polyp.pos ) / 2 #
		p.pos, p.growth_vector = self.find_bud_loc_2d(neighboring_polyp)

		for np in [self, neighboring_polyp]:
			theta = self.get_angle_between_vectors(p.growth_vector, np.growth_vector)
			#print "theta", theta * 180 / math.pi
			theta = theta * 1.2
			#print "theta", theta* 180 / math.pi
			#new_growth_vector = self.rotate( p.growth_vector, -1.0 * theta )
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

		self.colony.add_polyp(p)

		return

	def recalculate_growth_vector(self):

		if not self.next_polyp:
			return
		if not self.prev_polyp:
			return

		p1 = self.next_polyp
		p2 = self.prev_polyp

		vec = p1.pos - p2.pos

		new_vec = self.rotate(vec, math.pi / 2)
		self.growth_vector = new_vec / linalg.norm(new_vec)

		return

	def apply_new_growth_vector(self):
		self.growth_vector = self.new_growth_vector
		return

	def calculate_new_growth_vector(self):

		''' head or tail '''
		if self == self.colony.head_polyp:
			n1 = self.next_polyp
			n2 = n1.next_polyp
			#print "head:", n1.pos, n1.growth_vector, n2.pos, n2.growth_vector
			theta = self.get_angle_between_vectors(n1.growth_vector, n2.growth_vector)
			new_growth_vector = self.rotate(n1.growth_vector, theta)
			#print "head new growth vector", new_growth_vector
			self.new_growth_vector = new_growth_vector / linalg.norm(new_growth_vector)
			return

		if self == self.colony.tail_polyp:
			p1 = self.prev_polyp
			p2 = p1.prev_polyp
			theta = self.get_angle_between_vectors(p1.growth_vector, p2.growth_vector)
			new_growth_vector = self.rotate(p1.growth_vector, theta)
			self.new_growth_vector = new_growth_vector / linalg.norm(new_growth_vector)
			return

		p1 = self.prev_polyp
		n1 = self.next_polyp

		''' next to head or tail '''
		if p1 == self.colony.head_polyp or n1 == self.colony.tail_polyp:
			vec = n1.pos - p1.pos
			new_vector = self.rotate(vec, math.pi / 2)
			new_growth_vector = new_vector + self.growth_vector + p1.growth_vector + n1.growth_vector
			self.new_growth_vector = new_growth_vector / linalg.norm(new_growth_vector)
			return

		''' all other cases '''
		p2 = p1.prev_polyp
		n2 = n1.next_polyp

		polyp_list = [p2, p1, self, n1, n2]

		gv_list = []
		for i in range(1, len(polyp_list)):
			for j in range(len(polyp_list) - i):
				vec = polyp_list[i + j].pos - polyp_list[j].pos
				gv = self.rotate(vec, math.pi / 2)
				gv_list.append(gv)

		sum_gv = array([0, 0, 0], float)
		for gv in gv_list:
			sum_gv += gv
		new_gv = sum_gv / len(gv_list)
		self.new_growth_vector = new_gv / linalg.norm(new_gv)
		return

	def get_local_center(self, neighboring_polyp):

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

		arr_a = array([[a1, b1], [a2, b2]])
		arr_b = array([c1, c2])
		arr_x = linalg.solve(arr_a, arr_b)

		center = array([arr_x[0], 0, arr_x[1]], float)
		return center


	def grow_laterally(self):
		print "grow laterally"
		e = self.get_lower_edge_2d()
		print "peripheral budding", self.colony.config['peripheral_budding']
		if self.colony.config['peripheral_budding'] == ccfg.ID_ROUND:
			print "round"
			if e[2] < self.radius * 2:
				return

		e = self.get_outer_edge_2d()
		print "outer edge:", e

		p = CoralPolyp(self)

		if self.next_polyp:  # head
			p1 = self
			p2 = self.next_polyp

			p.next_polyp = self
			self.prev_polyp = p
			self.colony.head_polyp = p
		else:  #tail
			p1 = self
			p2 = self.prev_polyp

			p.prev_polyp = self
			self.next_polyp = p
			self.colony.tail_polyp = p

		if self.colony.config['peripheral_budding'] == ccfg.ID_PLATY:
			print "platy"
			p.growth_vector = array([0, 0, 1], float)
			sign = ( e[0] / math.fabs(e[0]) )
			p.pos = e + array([sign * p.radius, 0, 0], float)
		else:
			print "not platy"
			if e[2] > self.radius * 2:
				''' peripheral budding along colony surface '''
				center = p1.get_local_center(p2)
				v1 = p1.pos - center
				v2 = p2.pos - center
				#print "center", center, "v1", v1, linalg.norm( v1 ),  "v2", v2, linalg.norm( v2 )
				theta = p1.get_angle_between_vectors(v1, v2)
				#print "theta", theta
				new_vec = p1.rotate(v1, theta)
				new_vec /= linalg.norm(new_vec)
				new_vec *= ( linalg.norm(v1) - linalg.norm(v2) ) + linalg.norm(v1)
				new_pos = center + new_vec
				new_vec = new_vec / linalg.norm(new_vec)
				#print "new_vec", new_vec, "new_pos", new_pos
				#for i in range(3):
				#a[i] = new_vec[0,i]
				#b[i] = new_pos[0,i]

				#print "new:", new_vec, new_pos, a, b, center
				p.growth_vector = new_vec
				p.pos = new_pos

			else:
				print "should be encrusting"
				''' only encrusting '''
				z = e[2] / 2
				print "z:", z
				print
				sign = ( e[0] / math.fabs(e[0]) )
				x = e[0] + ( math.sqrt(self.radius ** 2 - z ** 2) ) * sign
				p.pos = array([x, 0, z], float)
				temp_vec = p.pos - e
				#p.growth_vector = array( [ sign * temp_vec[2], 0, temp_vec[0] ], float )
				p.growth_vector = self.rotate(temp_vec, math.pi * sign)
				#print "lateral:", self.pos, self.growth_vector, "new lateral:", p.pos, p.growth_vector
				#print "lateral growth", p1.pos, p2.pos

				#pass
				#p.pos = array( [ , , ], float )
		self.colony.add_polyp(p)
		print "lateral:", self.id, self.pos, self.growth_vector, "new lateral:", p.id, p.pos, p.growth_vector
		print "lateral:", p1.pos, p2.pos, p.pos

	def get_edge_2d(self):
		center = self.pos
		vec = self.growth_vector
		lateral_vec = array([vec[2] * -1, 0, vec[0]], float)
		lateral_vec_u = lateral_vec / linalg.norm(lateral_vec)
		edge1 = center + lateral_vec_u * self.radius
		edge2 = center - lateral_vec_u * self.radius
		return ( edge1, edge2 )

	def get_lower_edge_2d(self):
		(e1, e2) = self.get_edge_2d()
		if e1[2] < e2[2]:
			return e1
		else:
			return e2

	def get_outer_edge_2d(self):
		(e1, e2) = self.get_edge_2d()
		if self.next_polyp:
			return e1
		else:
			return e2

	def to_string(self):
		ret_str = ""
		ret_str += "[" + ", ".join([str(round(x * 10) / 10.0) for x in self.pos]) + "] / "
		ret_str += "[" + ", ".join([str(round(x * 10) / 10.0) for x in self.growth_vector]) + "]\n"
		return ret_str

	def print_to_image(self, img, origin, color="black"):

		imgdr = ImageDraw.Draw(img)
		if self.next_polyp:
			arr = []
			for p in [self.pos, self.next_polyp.pos]:
				arr.append(round(p[ccfg.X_INDEX] * self.colony.config['zoom']) + origin[0])
				arr.append(round(p[ccfg.Z_INDEX] * self.colony.config['zoom']) * -1 + origin[1])
			imgdr.line(arr, fill=color)

		#imgdr.line( arr, fill = color )
		#print "pos:", self.prev_pos, self.pos
		#self.prev_pos_list.append( self.prev_pos[:] )
		self.prev_pos[:] = self.pos[:]

		return

	def print_to_dc(self, dc, origin, color="black"):

		#dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
		#dc.Clear()
		#dw, dh = dc.GetSize()

		dc.SetPen(wx.Pen("black", 1))
		#print "zoom 1", self.colony.config['zoom']

		if self.next_polyp:
			#print "next polyp"
			x1 = round(self.pos[ccfg.X_INDEX] * self.colony.config['zoom']) + origin[0]
			y1 = round(self.pos[ccfg.Z_INDEX] * self.colony.config['zoom']) * -1 + origin[1]
			x2 = round(self.next_polyp.pos[ccfg.X_INDEX] * self.colony.config['zoom']) + origin[0]
			y2 = round(self.next_polyp.pos[ccfg.Z_INDEX] * self.colony.config['zoom']) * -1 + origin[1]
			#print "draw line"
			dc.SetPen(wx.Pen("green", 1))
			dc.DrawLine(x1, y1, x2, y2)


		#print "zoom 2", self.colony.config['zoom']
		trace = []

		#print self.annual_pos_list
		dc.SetPen(wx.Pen("black", 1))
		for p in self.pos_list:
			x1 = round(p[ccfg.X_INDEX] * self.colony.config['zoom'])
			y1 = round(p[ccfg.Z_INDEX] * self.colony.config['zoom']) * -1
			pt = wx.Point(x1, y1)
			trace.append(pt)
			#if self.selected:
			#print p
		x1 = round(self.pos[ccfg.X_INDEX] * self.colony.config['zoom'])
		y1 = round(self.pos[ccfg.Z_INDEX] * self.colony.config['zoom']) * -1
		#if self.selected:
		#    print self.pos

		pt = wx.Point(x1, y1)
		trace.append(pt)

		#print "zoom 3", self.colony.config['zoom']

		if self.selected:
			#print "selected", self.id
			dc.SetPen(wx.Pen("red", 1))

		dc.DrawLines(trace, xoffset=origin[0], yoffset=origin[1])

		if self.selected:
			#print "selected", self.id
			dc.SetPen(wx.Pen("red", 1))
			x1 = int(round(self.pos[ccfg.X_INDEX] * self.colony.config['zoom'])) + origin[0]
			y1 = int(round(self.pos[ccfg.Z_INDEX] * self.colony.config['zoom']) * -1) + origin[1]
			#print "x1, y1", x1, y1
			dc.DrawCircle(x1, y1, 5)
			x2 = int(round(self.pos[ccfg.X_INDEX] + self.growth_vector[ccfg.X_INDEX] * 10) * self.colony.config['zoom']) + \
			     origin[0]
			y2 = int(
				round(self.pos[ccfg.Z_INDEX] + self.growth_vector[ccfg.Z_INDEX] * 10) * self.colony.config['zoom']) * -1 + \
			     origin[1]

			dc.SetPen(wx.Pen("blue", 1))
			dc.DrawLine(x1, y1, x2, y2)

			txt = str(self.id) + ": " + ", ".join(
				[str(round(x * 10) / 10.0) for x in [self.pos[ccfg.X_INDEX], self.pos[ccfg.Z_INDEX]]])
			#print txt
			dc.DrawText(txt, x1 - 30, y1 - 50)
			txt = ", ".join(
				[str(round(x * 100) / 100.0) for x in [self.growth_vector[ccfg.X_INDEX], self.growth_vector[ccfg.Z_INDEX]]])
			#print txt
			dc.DrawText(txt, x1 - 30, y1 - 65)
			irradiance = round(self.irradiance * 100) / 100.0
			growth_rate = round(self.growth_rate * 100) / 100.0
			dc.DrawText(str(irradiance), x1 - 30, y1 - 80)
			dc.DrawText(str(growth_rate), x1 - 30, y1 - 95)
			#dc.DrawLine( 10, 10, 100, 100)
		return
