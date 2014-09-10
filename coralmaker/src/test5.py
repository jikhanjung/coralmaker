#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on Mar 9, 2014

@author: jikhanjung
'''

from JP_ProcessModel import Process, ProcessPool

f = open( "c:/example1.txt", 'r' )
lines = f.read().split( "\n")
f.close()

process_partial_order = {}

#print "total lines:", len( lines )
for ln in lines:
    time, wname, process = ln.split( "\t" )
    if wname not in process_partial_order.keys() :
        process_partial_order[wname] = []
    process_partial_order[wname].append( process )

order_in_progress = []
for k in process_partial_order.keys():
    order_in_progress.append( process_partial_order[k] )


ppool = ProcessPool()
idx = 0


for k in process_partial_order.keys():
    idx += 1
    l = process_partial_order[k] 
    if len( l ) == 0: continue
    #print idx, ": process count of", k, ":", len( l )
    p0 = ppool.get_process( l[0], k, True )
    if p0.is_new:
        #print "new", p0.pid
        ppool.add_head( p0.pid )
    #print "head_list", ppool.head_list[-1]
    for i in range(len(l)-1):
        p1 = ppool.get_process( l[i], k, True )
        p2 = ppool.get_process( l[i+1], k, True )
        p1.add_next( p2.pid )
        #if len( p2.prev ) == 0:
            #ppool.head_list.remove( p2.pid )
    #ppool.print_process_list()
    #print "------"
print "data loading done!"
#ppool.print_head_list()

#ppool.print_process_list()
ppool.print_stat()

''' remove all loops '''
print "check loop"
ppool.check_loop()

print "check loop done"
ppool.print_process_list()
ppool.print_stat()




if False:
    ''' set all prevs '''
    ppool.traverse_list_recur()
    
    ''' trim next '''
    ppool.trim_next()
    
    ''' print final flow '''
    ppool.print_flow()
