from collections import OrderedDict as  od
 
class LRUCache:
    
    def __init__( self, capacity ) :
        
        self.maxCapacity = capacity
        self.cache = od()
        
    def isPresent( self, chunkNumber) : 
        
        if( chunkNumber not in self.cache ) :
            return False 
        else:
            return True
        
    def get( self, chunkNumber ) : 
        
        if chunkNumber not in self.cache : 
            return -1    
        else :
            self.cache.move_to_end( chunkNumber) ### implements LRU principal used by shifting the key to the end (i.e most recently used )
            return self.cache[chunkNumber]
    
    def insert( self, key, value ) :
        
        self.cache[key] = value
        self.cache.move_to_end(key)

        if len(self.cache) > self.maxCapacity:
            self.cache.popitem(last = False)