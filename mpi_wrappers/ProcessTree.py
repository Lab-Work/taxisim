# -*- coding: utf-8 -*-
"""
Represents a tree of worker and manager processes for efficient parallel computing
on distributed systems.  Is most useful when a large number of workers are required
and when the amount of data that needs to be sent to them is large. In this case,
a hierarchy of managers can all send data to their children workers at the same time.

Created on Wed Jan 14 13:08:19 2015

@author: Brian Donovan briandonovan100@gmail.com
"""

from mpi4py import MPI


# Represents a hierarchy of worker and manager processes.  This facilitates fast dissemination of
# data to workers for efficient parallel computations
class ProcessTree:
    
    # Simple constructor.  Should be called by ALL MPI Processes
    # Params:
        # branching_factor - Max number of children each manager should have
        # height - The height of the tree
        # desired_leaves - should be less than branching_factor^height
        # batch_size - the number of jobs to be performed on each leaf
    def __init__(self, branching_factor, height, desired_leaves, batch_size=1):
        self.branching_factor = branching_factor
        self.height = height
        self.desired_leaves = desired_leaves
        self.batch_size = batch_size
        
        self._id = MPI.COMM_WORLD.Get_rank()
        self.parent_id = None
        self.child_ids = []
        self.leaf_sizes = []
    
    
       
    # Prepares the ProcessTree for use.  Should be called by ALL MPI Processes
    # The parent process will organize the remaining processes into a hierarchy by telling them
    # who their parent and children are.
    # This method will return for the master process, but workers will wait for instructions.
    def prepare(self):
        rank = MPI.COMM_WORLD.Get_rank()
        if(rank==0):
            # If we are the main process, build the tree to plan the computation
            self.root, status = grow_tree(self.branching_factor, self.height, self.desired_leaves)
            # Tell all of the other processes who their parent and children are
            self._send_parents_and_children(self.root)

        # Wait for the main process to tell us who our family is
        # Note that the main process tells itself
        self.parent_id, self.child_ids, self.leaf_sizes = MPI.COMM_WORLD.recv(source=0)
        # print ( str(self._id) + ") Parent: " + str(self.parent_id) + "  Children: " + str(self.child_ids) + "  Leaf_sizes: " + str(self.leaf_sizes))
    
        if(rank > 0):
            self._wait_for_instructions()
    
    
    # Evaluates a function on many different inputs in parallel. It should
    # only be called by the master process. Does not return until ALL child
    # processes are complete
    # Params:
        # func - the function to be run
        # const_args - Any arguments that are the same in all evaluations of the function.
            # Can be a tuple or list if multiple arguments are required
        # args_list - A list of arguments that may change between each evaluation.
            # Can be a list of lists or tuples if the function requires multiple inputs
    def map(self, func, const_args, args_list):
        if(MPI.COMM_WORLD.Get_rank()==0):
            # The max number of jobs we can do in parallel is self.desired_leaves
            # So we will cut args_list into slices of this size or smaller and process
            # them individually
            start_pos = 0
            while(start_pos < len(args_list)):
                end_pos = start_pos + self.desired_leaves # Create slice of correct size
                end_pos = min(end_pos, len(args_list)) # Avoid array overflow
                self._map(func, const_args, args_list[start_pos:end_pos])
                
                # Advance to the next slice
                start_pos = end_pos
        else:
            raise Exception("close() should only be called by master process.")
    
    # Closes the ProcessTree, allowing all of the MPI Processes to escape.  Should only
    # be called by the master process.
    def close(self):
        if(MPI.COMM_WORLD.Get_rank()==0):
            self._close()
        else:
            raise Exception("close() should only be called by master process.")
    
    
    # Internal method which tells all of the children of this process to close.
    def _close(self):
        # Send the close message to each child
        for i in self.child_ids:
            MPI.COMM_WORLD.send("close", dest=i)
            
    # Internal function which splits arg_list into pieces, and sends the corresponding
    # jobs to the children nodes.
    # Params:
        # func - the function to be run
        # const_args - Any arguments that are the same in all evaluations of the function.
            # Can be a tuple or list if multiple arguments are required
        # args_list - A list of arguments that may change between each evaluation.
            # Can be a list of lists or tuples if the function requires multiple inputs
    def _map(self, func, const_args, args_list):
        # We must send the appropriate number of jobs to each child.  Since the tree
        # may not be perfectly symmetric, each child may not receive the same number of jobs.
        # The number of jobs should be the nuumber of leaf nodes beneath that child
        # (or 1 if that child is a leaf)
        start_pos = 0
        for i in xrange(len(self.child_ids)):
            # Create a slice that is the right size for that child
            end_pos = start_pos + self.leaf_sizes[i] * self.batch_size
            # Avoid array out of bounds, may send a job that is smaller than the capacity
            end_pos = min(end_pos, len(args_list))
            
            child_args = args_list[start_pos:end_pos] # Slice the args list
            
            # Send the data
            MPI.COMM_WORLD.send((func, const_args, child_args), dest=self.child_ids[i])
            
            start_pos = end_pos # Advance to the next slice
            
            # Out of jobs - the remaining children are unnecessary
            if(start_pos >= len(args_list)):
                break
        num_useful_children = i+1

        # Free memory - we don't need the data anymore
        del(const_args)
        del(args_list)

        
        # Now wait for all children to inform us that they are done
        # Only wait on children who were given a job (useful children)
        for i in xrange(num_useful_children):
            done_msg = MPI.COMM_WORLD.recv(source=self.child_ids[i])
            done_msg += ""
        
        # Finally, inform parent that we are done
        if(self.parent_id!=None):
            MPI.COMM_WORLD.send("done", dest=self.parent_id)
    
    
    
    # Internal recursive method which should only be called by the MASTER MPI Process
    # It tells each process who its parent and children are
    # Params:
        # ptnode - a node of the virtual process tree
    def _send_parents_and_children(self, ptnode):
        # Each PTNode's _id field corresponds to a MPI process id
        # Tell that process who its parents and children are, and how many
        # leaves are below each of its children
        if(ptnode.parent==None):
            parent_id = None
        else:
            parent_id = ptnode.parent._id
        child_ids = ptnode.get_child_ids()
        leaf_sizes = ptnode.get_child_leaf_sizes()
        
        MPI.COMM_WORLD.send((parent_id, child_ids, leaf_sizes), dest=ptnode._id)
        
        #Make the recursive call so the rest of the tree is also informed
        for child in ptnode.children:
            self._send_parents_and_children(child)
    
    # Internal method which should only be called by MPI Processes OTHER THAN THE MASTER
    # It loops forever, waiting for the master to give it jobs or tell it to close
    def _wait_for_instructions(self):
        
        while(True):
            #Receive data from the parent
            data = MPI.COMM_WORLD.recv(source=self.parent_id)
            
            if(data=="close"):
                # First, kill all of the children
                self._close()
                # Then, exit the loop
                break
            else:
                # Unpack the data
                func, const_args, args_list = data
                
                if(self.child_ids==[]):
                    # If this is a leaf node, just run the function on the given inputs
                    # If batch_size > 1, then run the function several times
                    for args in args_list:
                        func(const_args, args)
                        
                    # Inform the parent that we are done
                    MPI.COMM_WORLD.send("done", dest=self.parent_id)
                else:
                    # If this is an internal node, split the args_list and send
                    # Everything to the children
                    self._map(func, const_args, args_list)
    
        

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
    parent = None
    leaf_size = 0    
    
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
        self.children = []
        if(depth==status.height):
            self.is_leaf = True
            status.num_leaves += 1
            self.leaf_size = 1
            # Return True since this Node is useful
            return True
        
        
        # Recursively grow children (# of children = bf)
        # We will also sum up the leaf sizes of the children to make this node's leaf size
        self.leaf_size = 0
        for i in range(status.bf):
            potential_child = PTNode()
            # Make the recursive call
            success = potential_child.grow(status, depth+1)
            #Only add that node to the list of children if it is useful, otherwise discard
            if(success):
                potential_child.parent = self
                self.children.append(potential_child)
                self.leaf_size += potential_child.leaf_size

        # Return true since this node (and at least one of its children) is useful
        # This assumption is valid becaue we would have returned False earlier if
        # there were enough leaves.  Therefore, if we got to here, we had to make
        # more recursive calls and grow more leaves.
        return True
    
    # Returns the id numbers of each of this PTNode's children
    def get_child_ids(self):
        return [child._id for child in self.children]
    
    # Returns the number of leaves underneath each of this PTNode's children
    def get_child_leaf_sizes(self):
        return [child.leaf_size for child in self.children]


# A simple function for testing purposes
def times(a,b):
    rank = MPI.COMM_WORLD.Get_rank()
    print str(a) + " x " + str(b).rjust(3,"0") + " = " + str(a*b)

#  A simple test
if(__name__=="__main__"):
    # Build and prepare the process tree 
    t = ProcessTree(3,3,15, batch_size=4)
    t.prepare()
    
    
    if(MPI.COMM_WORLD.Get_rank()==0):
        a = 3 # Constant arguments
        b_list = range(101) # List of arguments
        t.map(times, a, b_list)
        t.close()
    
