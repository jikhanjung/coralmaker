#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Oct 26, 2013

@author: jikhanjung
'''
from ggplot import *


print (ggplot(aes(x='date', y='beef'), data=meat) + \
    geom_point())

plt.show(1)

