from .node import Node

class MinHeap:
    def __init__(self):
        """
        On this implementation the heap list is initialized with a value
        """
        self.heap_list = [Node((-1,-1))]
        self.current_size = 0
 
    def sift_up(self, i):
        """
        Moves the value up in the tree to maintain the heap property.
        """
        # While the element is not the root or the left element
        while i // 2 > 0:
            # If the element is less than its parent swap the elements
            if self.heap_list[i].f < self.heap_list[i // 2].f:
                self.heap_list[i].f, self.heap_list[i // 2].f = self.heap_list[i // 2].f, self.heap_list[i].f
            # Move the index to the parent to keep the properties
            i = i // 2
 
    def insert(self, k):
        """
        Inserts a value into the heap
        """
        # Append the element to the heap
        self.heap_list.append(k)
        # Increase the size of the heap.
        self.current_size += 1
        # Move the element to its position from bottom to the top
        self.sift_up(self.current_size)
 
    def sift_down(self, i):
        # if the current node has at least one child
        while (i * 2) <= self.current_size:
            # Get the index of the min child of the current node
            mc = self.min_child(i)
            # Swap the values of the current element is greater than its min child
            if self.heap_list[i].f > self.heap_list[mc].f:
                self.heap_list[i].f, self.heap_list[mc].f = self.heap_list[mc].f, self.heap_list[i].f
            i = mc
 
    def min_child(self, i):
        # If the current node has only one child, return the index of the unique child
        if (i * 2)+1 > self.current_size:
            return i * 2
        else:
            # Herein the current node has two children
            # Return the index of the min child according to their values
            if self.heap_list[i*2].f < self.heap_list[(i*2)+1].f:
                return i * 2
            else:
                return (i * 2) + 1
                
    def empty(self):
        return len(self.heap_list) == 1
        
 
    def pop(self):
        # Equal to 1 since the heap list was initialized with a value
        if len(self.heap_list) == 1:
            return -1
 
        # Get root of the heap (The min value of the heap)
        root = self.heap_list[1]
 
        # Move the last value of the heap to the root
        self.heap_list[1] = self.heap_list[self.current_size]
 
        # Pop the last value since a copy was set on the root
        *self.heap_list, _ = self.heap_list
 
        # Decrease the size of the heap
        self.current_size -= 1
 
        # Move down the root (value at index 1) to keep the heap property
        self.sift_down(1)
 
        # Return the min value of the heap
        return root
            
def heuristic(node, end_position):
    return ((end_position[0] - node.position[0]) ** 2) + ((end_position[1] - node.position[1]) ** 2)

def a_star(source, destiny, m, n, blocks):

    start_node = Node(source)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(destiny)
    end_node.g = end_node.h = end_node.f = 0
    
    open_list = MinHeap()
    closed_list = []
    
    open_list.insert(start_node)
    
    while not open_list.empty():
        
        current_node = open_list.pop()
        closed_list.append(current_node)
        
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.fromNode
            return path[::-1]
        
        neighbors = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            # Make sure we are inbounds
            if node_position[0] > m - 1 or node_position[0] < 0 or node_position[1] > n - 1 or node_position[1] < 0:
                continue
            
            # Check if we can actually walk through node_position
            if node_position in blocks:
                continue
            
            new_node = Node(node_position)
            neighbors.append(new_node)
        
        i = -1
        for neighbor in neighbors:
            i += 1
            tentative_distance = current_node.g + 1
            if tentative_distance < neighbor.g:
                neighbor.fromNode = current_node
                neighbor.g = tentative_distance
                neighbor.f = neighbor.g + heuristic(neighbor, destiny)

                if neighbor in closed_list:
                    continue
            
                if not neighbor in open_list.heap_list:
                    open_list.insert(neighbor)
            
            