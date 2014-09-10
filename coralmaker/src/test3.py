#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 24, 2013

@author: jikhanjung
'''

import math
from numpy import *

Y_INDEX = 1

def rotate(vec,theta):
        rotation_matrix = matrix( [ [ math.cos( theta ), 0, math.sin( theta )] , 
                                    [ 0, 1, 0 ],
                                    [-1 * math.sin(theta ), 0, math.cos(theta) ],
                                ] )
        new_vec = dot( vec, rotation_matrix )
        vec = squeeze( asarray( new_vec[0] ) )
        return vec

def get_angle_between_vectors( v1, v2 ):
        
        cross_product = cross( v1, v2 )
        sin_theta = cross_product[Y_INDEX] / ( linalg.norm( v1 ) * linalg.norm( v2 ) )
        print "sin_theta", sin_theta
        #if sin_theta > 0:
            #print "plus"
        #else:
            #print "minus"
        theta = math.asin( sin_theta )
        return theta
def radian_to_degree( radian ):
    return radian * 180 / math.pi

vec1 = [ -9.3, 0, 16.9 ]
vec2 = [ -7.1, 0, 18.5 ]

theta = get_angle_between_vectors( vec1, vec2 )
print radian_to_degree( theta )
vec3 = rotate( vec1, theta )
print vec3
vec = squeeze( asarray( vec3[0] ) )
print vec

theta = get_angle_between_vectors( vec, vec1 )
print radian_to_degree( theta )

vec1 = [ 1, 0, 0 ]
vec2 = [1, 0, 1 ]


theta = get_angle_between_vectors( vec1, vec2 )
print radian_to_degree( theta )


print 0.785 * ( 180 / 3.14159 )
