#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Sep 28, 2013

@author: jikhanjung
'''

import math

from numpy import *


ATTENUATION_COEFF = 4.6 / 50.0
SURFACE_IRRADIANCE = 1361
MAX_IRRADIANCE = 100
REFLECTION_RATE = 0.05
Y_INDEX = 1


def rotate(vec, theta):
	rotation_matrix = matrix(
		[[math.cos(theta), 0, math.sin(theta)], [-1 * math.sin(theta), 1, math.cos(theta)], [0, 0, 1]])
	print vec
	print rotation_matrix
	new_vec = dot(vec, rotation_matrix)
	return new_vec


def get_angle_between_vectors(v1, v2):
	cross_product = cross(v1, v2)
	sin_theta = cross_product[Y_INDEX] / ( linalg.norm(v1) * linalg.norm(v2) )
	print sin_theta
	if sin_theta > 0:
		print "plus"

	else:
		print "minus"
	theta = math.asin(sin_theta)
	return theta


def get_irradiance(depth, grow_vector):
	vec = grow_vector / linalg.norm(grow_vector)
	cos_val = vec[2]
	# print cos_val

	radiance_base = SURFACE_IRRADIANCE * math.exp(-1 * ATTENUATION_COEFF * depth)  #Wm-2

	floor_reflection = radiance_base * REFLECTION_RATE
	direct_irradiance = radiance_base * cos_val

	total_irradiance = floor_reflection + direct_irradiance

	if total_irradiance > MAX_IRRADIANCE:
		return 1
	else:
		return total_irradiance / MAX_IRRADIANCE

	return 1


def find_bud_loc_2d(v1, v2, p1, p2):
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
	print center
	# print p1, p2, "center:", center
	radius = ( linalg.norm(p1 - center) + linalg.norm(p2 - center) ) / 2
	print radius
	vec = ( ( p1 - center ) + ( p2 - center ) ) / 2
	new_loc = center + ( vec / linalg.norm(vec) ) * radius
	#print p1, p2, "center:", center, "new:", new_loc
	return new_loc


p1 = array([-5, 0, 2.3], float)
p2 = array([0, 0, 3], float)
v1 = array([-3, 0, 4], float)
v2 = array([0, 0, 1], float)

print p1, p2
l = find_bud_loc_2d(v1, v2, p1, p2)
print l

print "angle"
print v1, v2
t = get_angle_between_vectors(v1, v2)

v3 = rotate(v1, t)
print v3
if False:
	DEPTH = [1, 20, 50]
	vec = [array([0, 0, 1], float), array([1, 0, 1], float), array([1, 0, 0], float)]

	for d in DEPTH:
		for v in vec:
			i = get_irradiance(d, v)
			print d, v, i, 1 - math.exp(-1.0 * i * 10)
		print