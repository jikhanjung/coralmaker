'''
Created on Mar 9, 2014

@author: jikhanjung
'''
from JP_ProcessModel import Process, ProcessPool

list1 = [ 1, 2, 3, 5, 12, 6, 7, 21 ]
list2 = [ 3, 12, 13, 6, 5 ]
list3 = [ 1, 5, 7, 8, 21 ]
list4 = [ 8, 9, 15, 17]
list_list = [list1, list2, list3, list4]
if len(list_list) % 2 != 0: 
    list_list.append( [] )
list_len = len( list_list )
print list_len 
print list_list

ppool = ProcessPool()
ppool.set_debug(True)

for l in list_list:
    if len( l ) == 0: continue
    print "original_list", l
    p0 = ppool.get_process( l[0] )
    if p0.is_new:
        print "new", p0.pid
        ppool.add_head( p0.pid )
    print "head_list", ppool.head_list[-1]
    for i in range(len(l)-1):
        p1 = ppool.get_process( l[i] )
        p2 = ppool.get_process( l[i+1] )
        p1.add_next( p2.pid )
        if p2.pid in ppool.head_list:
            ppool.head_list.remove( p2.pid )
        p2.add_prev( p1.pid )
        #is_okay = p2.add_prev_list( l[:i+1] )
            
    #ppool.print_process_list()
    print "------"
ppool.print_head_list()

ppool.print_process_list()
ppool.print_stat()

print "check loop"
ppool.check_loop()

ppool.print_process_list()
ppool.print_stat()

#print "traverse_list_recur"
#print ppool.head_list
ppool.traverse_list_recur()

#ppool.print_process_list()
#ppool.print_stat()

ppool.trim_next()

#ppool.print_process_list()
#ppool.print_stat()


ppool.print_flow()
#print ppool.loop_list



#ppool.print_process_list()
#ppool.print_stat()
