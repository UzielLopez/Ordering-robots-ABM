class Node:
    def __init__(self, position):
        
        self.index = None
        self.fromNode = None
        self.position = position
                
        self.g = float('inf')
        self.h = float('inf')
        self.f = float('inf')
    
    # We will consider two instances of nodes equal if their position is the same, even if they are not
    # the same object
    def __eq__(self, other):
        return self.position == other.position