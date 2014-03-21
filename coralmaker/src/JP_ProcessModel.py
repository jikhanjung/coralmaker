'''
Created on Mar 12, 2014

@author: jikhanjung
'''
'''
Created on Mar 9, 2014

@author: jikhanjung
'''


class Process():
    def __init__(self, pid, pool):
        self.next = []
        self.prev = []
        self.pid = pid
        self.is_new = True
        self.pool = pool
        self.debug = False
        self.loop_check_done = False
        self.traverse_done = False
        self.wafer_list = []
        self.count = 0
    def check_new(self):
        if self.is_new:
            self.is_new = False
            return True
        else:
            return False
    def add_next(self,a_pid):
        if a_pid not in self.next:
            self.next.append( a_pid )
    def add_prev(self, a_pid):
        if a_pid not in self.prev:
            self.prev.append( a_pid )
    def add_prev_loop_check(self,a_pid):
        #if self.get_debug(): print "add prev", a_pid, "to", self.pid 
        if a_pid == self.pid:
            if self.get_debug(): print "loop!", a_pid
            return False
        if a_pid not in self.prev:
            self.prev.append( a_pid )
        return True

    def add_prev_list(self,pid_list ):
        #print "add prev list", self.pid, pid_list
        for pid in pid_list:
            self.add_prev( pid )
     
    def add_prev_list_old(self,pid_list, start_pid=-1 ):
        print "add prev list", self.pid, pid_list, start_pid
        if start_pid < 0:
            start_pid = self.pid
        elif start_pid == self.pid:
            return
        for pid in pid_list:
            pp = self.pool.get_process( pid )
            if self.pid in pp.prev:
                print "loop!", self.pid, "is in", pid,"'s prev:", pp.prev
                continue
            self.add_prev( pid )
        if len( self.next ) > 0:
            for nid in self.next:
                np = self.pool.get_process( nid )
                np.add_prev_list( pid_list, start_pid )
                
        return True
    def traverse_and_trim(self, depth=0,so_far_pid_list=[]):
        if depth==99: return 
        next_list = self.next
        for next_id in next_list:
            #print "checking", self.pid, next_id
            check_list = next_list[:]
            check_list.remove(next_id)
            p = self.pool.get_process( next_id )
            for pid_to_check in check_list: 
                if p.has_next( pid_to_check ):
                    next_list.remove( pid_to_check )
            so_far_pid_list.append( p.pid )
            p.traverse_and_trim( depth+1, so_far_pid_list )
            so_far_pid_list.pop()

        #self.next = next_list
    def get_debug(self):
        return self.pool.get_debug()
    #def has_next(self, a_pid):
    def trim_next(self):
        for cid in self.next:
            p = self.pool.get_process( cid )
            next_list = self.next[:]
            next_list.remove( cid )
            for nid in next_list:
                if nid in p.prev:
                    self.next.remove( cid )
        
                
    def has_next_iter(self, a_pid ):
        if self.get_debug(): print self.pid, a_pid
        checked_list = []
        
        list_to_check = self.next[:]        
        
        i = 1

        if self.get_debug(): print i, len( list_to_check ), list_to_check
        while i <= len( list_to_check ):
            nid = list_to_check[i-1]
            if self.get_debug(): print "pid:", self.pid, "a_pid", a_pid, "nid", nid, "i:",  i, "/", len( list_to_check ), list_to_check, checked_list
            if a_pid == nid:
                return True
            else:
                i+=1
                if nid not in checked_list:
                    p = self.pool.process_hash[nid]
                    list_to_check.extend( p.next )
                    checked_list.append( nid )
                
        return False
        
    def has_next(self, a_pid, depth=0 ):
        if depth==99: return False
        for nid in self.next:
            if a_pid == nid: return True
            else:
                return self.pool.get_process( nid ).has_next( a_pid, depth+1 )
        return False
    def traverse_recur(self,prev_pid_list = []):
        #print "traverse", self.pid, prev_pid_list

        #if self.traverse_done:
        #    pass
        #    return
        
        if self.pid in prev_pid_list:
            print "loop!", self.pid
            return

        self.add_prev_list( prev_pid_list )
        prev_pid_list.append( self.pid )

        for nid in self.next:
            np = self.pool.get_process( nid )
            np.traverse_recur( prev_pid_list )

        prev_pid_list.pop()
        #self.traverse_done = True
        return
        
    def check_loop(self, cid=-1, prev_pid_list=[] ):
        #print "check loop", self.pid, cid, prev_pid_list
        if self.loop_check_done:
            return False
        if cid < 0:
            cid = self.pid
        elif cid == self.pid:
            print "yes, this is loop!", self.pid, cid, prev_pid_list
            return True
        elif self.pid in prev_pid_list:
            #print "has loop!", self.pid, cid, prev_pid_list
            return True

        if len( self.next ) == 0:
            self.loop_check_done = True
            return False
            
        has_loop = False
        prev_pid_list.append( self.pid )
        for nid in self.next:
            if nid in prev_pid_list:
                print "loop ahead", nid, ".. deleting loop"
                self.next.remove(nid)
                continue
            np = self.pool.get_process( nid )
            rv = np.check_loop( cid, prev_pid_list )
            if rv:
                has_loop = rv
                break

        prev_pid_list.pop()
        if not has_loop:
            self.loop_check_done = True
            
        return has_loop

    def print_process(self):
        print self.pid, self.count, self.next, self.prev
    def print_flow(self, process_flow):
        process_flow.append( self.pid )
        if len( self.next ) == 0:
            print process_flow
        for nid in self.next:
            p = self.pool.get_process( nid )
            p.print_flow( process_flow)
        process_flow.pop()

class ProcessPool():
    def __init__(self):
        self.head_list = []
        self.process_list = []
        self.process_hash = {}
        self.debug = False
        self.loop_list = []
    def trim_next(self):
        for p in self.process_list:
            p.trim_next()
    def set_debug(self,a_debug):
        self.debug = a_debug
    def get_debug(self):
        return self.debug
    def add_head(self,a_pid):
        self.head_list.append( a_pid )        
    def get_process(self,pid, wafer="", count=False):
        #print "pid:", pid
        if pid in self.process_hash.keys():
            p = self.process_hash[pid]
            p.is_new = False
            if count:
                p.count += 1
                if wafer != "":
                    p.wafer_list.append( wafer )
            return p 
        else:
            #print "new process", pid
            p = Process(pid, self)
            self.process_hash[pid] = p
            if count:
                p.count += 1
                if wafer != "":
                    p.wafer_list.append( wafer )
            self.process_list.append( p )
            return p
    def print_process_list(self, level=0):
        for p in self.process_list:
            p.print_process()
    def print_head_list(self):
        for p in self.head_list:
            if self.get_debug(): print "head pid", p

    def traverse_list_recur(self):
        #print "traverse list"
        for pid in self.head_list:
            p = self.get_process( pid )
            p.traverse_recur()
        

    def trim_list_recur(self):
        pid_list_to_check = []
        pid_list_to_check.extend( self.head_list )
        i = 0
        while True:
            
            p = self.get_process( pid_list_to_check[i] )
            p.traverse_and_trim_recur()

            pid_list_to_check.extend( p.next )
            i += 1            
                
            
    
    def trim_list(self):
        for head_pid in self.head_list:
            p = self.process_hash[head_pid]
            p.traverse_and_trim()

    def trim_list_iter(self):
        
        for head_pid in self.head_list:
            p = self.process_hash[head_pid]
            while True:
                if self.get_debug(): print "checking pid", p.pid
                for nid in p.next:
                    next_list = p.next[:]
                    next_list.remove( nid )
                    #np = self.process_hash[nid]
                    for cid in next_list:
                        cp = self.process_hash[cid]
                        if self.get_debug(): print "check if", cid, "is next of", nid
                        if nid in cp.prev:
                            p.next.remove( cid )
                            if self.debug: print "yes", p.next
                if len( p.next ) == 0:
                    return        
                p = self.process_hash[p.next[0]]
                
                #if len( p.next ) == 1:
                #    if self.get_debug(): print "okay"
                    

    def trim_list_iter2(self):
        already_been_there= []
        pid_list_to_visit=[]
        idx_list=[]
        pid_list_to_visit.append( self.head_list )
        idx_list.append( 0 )
        level = 0
        idx = 0
        while True:
            print level, idx, pid_list_to_visit
            curr_list = pid_list_to_visit[level]
            idx = idx_list[level]
            found_loop = False
            for pid in curr_list[idx:]:
                if pid in already_been_there:
                    print "next pid", pid, ", we've been there..", already_been_there
                    found_loop = True
                    continue
                p = self.get_process(pid)
                
                if len( p.next ) > 0:
                    if len( p.next ) > 1:
                        print "trim next", p.pid, p.next
                        for nid in p.next:
                            next_list = p.next[:]
                            next_list.remove( nid )
                            for cid in next_list:
                                cp = self.get_process(cid)
                                if self.get_debug(): print "check if", cid, "is next of", nid
                                if nid in cp.prev:
                                    p.next.remove( cid )
                                    if self.debug: print "yes", p.next
                        print "trimmed next", p.pid, p.next
                    else:
                        if found_loop == True:
                            level -= 1
                            idx_list[level] += 1
                            break
                        
                    pid_list_to_visit.append( p.next )
                    idx_list[-1] = idx
                    idx_list.append( 0 )
                    level += 1
                    already_been_there.append( p.pid )
                    break
                elif len( p.next ) == 0:
                    level -= 1
                    idx_list[level] += 1
                    break
                idx += 1
            #if found_loop == True:
    def check_loop(self):
        for pid in self.head_list:
            p = self.get_process( pid )
            p.check_loop()
    def print_flow(self):
        for pid in self.head_list:
            process_flow = []
            process_flow.append( pid )
            p = self.get_process( pid )
            for nid in p.next:
                p = self.get_process(nid)
                p.print_flow( process_flow )

    def print_stat(self):
        print "total next:", sum( [ len( p.next ) for p in self.process_list ])
        print "total process:", len( self.process_list )
        stat = {}
        for p in self.process_list:
            k = len( p.next )
            if k in stat.keys():
                stat[k] += 1
            else:
                stat[k] = 1
        ks = stat.keys()
        ks.sort()
        for i in ks:
            print i, stat[i]
        print "head:", self.head_list
