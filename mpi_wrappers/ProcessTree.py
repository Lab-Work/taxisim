# -*- coding: utf-8 -*-
"""
Represents a tree of worker and manager processes for efficient parallel computing
on distributed systems.  Is most useful when a large number of workers are required
and when the amount of data that needs to be sent to them is large. In this case,
a hierarchy of managers can all send data to their children workers at the same time.

Created on Wed Jan 14 13:08:19 2015

@author: Brian Donovan briandonovan100@gmail.com
"""




# Work in progress
class ProcessTree:
    def __init__(self, branching_factor):
        pass



# Grows a tree of a given shape and size, if possible
# Params:
    # bf - the desired branching factor of the tree
    # height - the desired height of the tree
    # desired_leaves - should be less than bf^height.  The tree will stop growing
        # once this many leaves have been produced
# Returns:
    # root - a PTNode that represents the root of the tree
    # status - a GrowStatus that contains some stats about the tree's size
def grow_tree(bf, height, desired_leaves):
    status = GrowStatus(bf, height, desired_leaves)
    root = PTNode()
    root.grow(status)
    
    return root, status

# Tracks stats about the status of a tree's growing progress
class GrowStatus:
    num_nodes = 0
    num_leaves = 0
    def __init__(self, bf, height, desired_leaves):
        self.bf = bf
        self.height = height
        self.desired_leaves = desired_leaves
        
        

# Represents a Node in a tree, which is used to organize MPI processes into a hierarchy.
# Note that there are no MPI calls in this class.  The master process should just build
# a tree of PTNodes in order to plan the execution strategy.
class PTNode:
    is_leaf = False
    _id = -1
    
    def __init__(self):
        pass
    
    # Recursively grows children nodes until the tree is big enough
    # Will stop growing once the tree is tall enough or has enough leaves
    # Params:
        # status - A GrowStatus that will be modified as the tree grows
        # depth - How deep into the tree is this node?  Root is 0, children are 1, and so on
    # Returns - True if this Node is useful (i.e. it expanded successfully), or
        # False if we already have enough leaves and the tree is done growing.
    def grow(self, status, depth=0):
        
        
        #Tree is already big enough - stop growing it
        if(status.num_leaves >= status.desired_leaves):
            # Return false since this Node is not useful
            return False
        
        # Continue growing
        # Hand out an ID number to this node, and count it towards the total number of nodes
        self._id = status.num_nodes
        status.num_nodes += 1        
        
        
        # This node is a leaf - mark it as such and end the recursion
        if(depth==status.height):
            self.is_leaf = True
            status.num_leaves += 1
            # Return True since this Node is useful
            return True
        
        
        # Recursively grow children (# of children = bf)
        self.children = []
        for i in range(status.bf):
            potential_child = PTNode()
            # Make the recursive call
            success = potential_child.grow(status, depth+1)
            #Only add that node to the list of children if it is useful, otherwise discard
            if(success):
                self.children.append(potential_child)

        # Return true since this node (and at least one of its children) is useful
        # This assumption is valid becaue we would have returned False earlier if
        # there were enough leaves.  Therefore, if we got to here, we had to make
        # more recursive calls and grow more leaves.
        return True


#  A simple test
if(__name__=="__main__"):
    root, status = grow_tree(22,5,75000)
    print (status.num_nodes, status.num_leaves)
