# -*- coding: utf-8 -*-
"""
A KD-Tree, which can be used on any array-like objects
i.e. objects that implement __getitem__() and __len__()
This can be used to quickly perform nearest neighbor queries, and partition data
points into rectangles with roughly the same number of points in each region.
Created on Fri Dec  5 16:30:53 2014

@author: brian
"""
from itertools import imap


# A KD-Tree which supports nearest-neighbor lookup.  It also has a get_leaf() function
# which can be used to determine if two nodes are in the same region.
# Note that the children of a KD-Tree are also KD-Trees. We make no distinction
# between the nodes of the tree and the tree itself.  Leaf nodes are just KDTrees
# whose chidren are None, and store data points in them
class KDTree:
    split_dim = 0
    split_val = 0
    low_child = None
    hi_child = None
    
    #Initializes the kd-tree with some data.  Will recursively grow children trees
    #If there is too much data
    #Params:
        # data - A list of objects, which must implement __getitem__() and __len__()
        # split_dim - which dimension should we split on (the children will split on the next dimension and so on)
        # leaf_size - stop splitting when a child has less than this many data points
    def __init__(self, data, split_dim=0, leaf_size=100):
        
        self.split_dim = split_dim
        if(len(data) <= leaf_size):
            #Not enough data - this tree is a leaf node
            self.data = data
        else:
            num_dimensions = len(data[0])
            # Identify the median as the split point
            # TODO: This is currently done the "easy way".
            # A linear time algorithm or simpler criteria could be used
            data.sort(key = lambda x: x[split_dim])            
            mid = len(data) / 2
            self.split_val = data[mid][split_dim]
            
            #Child trees will split on the next dimension (cycle after running out)
            next_dim = (self.split_dim + 1) % num_dimensions
            
            #Recursively grow children
            self.low_child = KDTree(data[:mid], next_dim, leaf_size)
            self.hi_child = KDTree(data[mid:], next_dim, leaf_size)
            self.data = None
    
    # Returns the leaf node that a query point is geometricaly in
    # Params:
        # point - any array-like object.  Not necessarily a point used to grow the tree
    # Returns:
        # A KDTree object, which represents the leaf node.
    def get_leaf(self, point):
        #This is a leaf
        if(self.low_child==None and self.hi_child==None):
            return self
        
        #This is not a leaf - figure out which child contains the point
        point_val = point[self.split_dim]
        
        #Recursively call that child
        if(point_val < self.split_val):
            return self.low_child.get_leaf(point)
        else:
            return self.hi_child.get_leaf(point)
    
    # Finds the data point in the KDTree which is nearest to a query point
    # Params:
        # point - The query point, any array-like object
        # max_squared_dist - An upper bound on the (squared) neighbor distance.
        #   Subtrees That are further away than this will not be explored
    # Returns:
        # The data point which is nearest to the query point
    def nearest_neighbor_query(self, point, max_squared_dist=float('inf')):
        
        #if this is a leaf, search through the points
        if(self.data != None):
            best_squared_dist = max_squared_dist
            best_point = None
            for d in self.data:
                #dist = squared_dist(point, d)
                diff = imap(float.__sub__, point, d)
                dist = sum(map(lambda x: x*x, diff))                
                
                
                
                if(dist < best_squared_dist):
                    best_squared_dist = dist
                    best_point = d
            self.calls = 1
            return best_point, best_squared_dist
        
        
        #This is an internal node.  Determine which branch the point is in (close branch)
        #And which one it is not (far branch).  The nearest neighbor is probably in the close
        #branch, but there is a possibility that it is in the far branch
        point_val = point[self.split_dim]
        
        if(point_val < self.split_val):
            close_branch = self.low_child
            far_branch = self.hi_child
        else:
            close_branch = self.hi_child
            far_branch = self.low_child
        
        #First search the close branch for the nearest neighbor and its distance
        best_point, best_squared_dist = close_branch.nearest_neighbor_query(point, max_squared_dist)
        self.calls = close_branch.calls + 1
        
        #If the query point is close to the border, the nearest neighbor might still be in the far branch
        #However, if the border is farther away than the best match so far, there is no need to search it
        border_dist = (self.split_val - point[self.split_dim])**2
        if(border_dist < best_squared_dist):
            candidate_point, candidate_squared_dist = far_branch.nearest_neighbor_query(point, best_squared_dist)
            
            #If we found a better match in the far branch, replace the old one
            if(candidate_squared_dist < best_squared_dist):
                best_point = candidate_point
                best_squared_dist = candidate_squared_dist
            
            self.calls += far_branch.calls
        
        #Return the best match that we have found so far
        return best_point, best_squared_dist
    
    def get_height(self):
        if(self.low_child==None and self.hi_child==None):
            return 1
        else:
            return min(self.low_child.get_height(), self.hi_child.get_height()) + 1

# For testing purposes - finds the nearest neighbor to a query point brute force style
# It should return the same value as KDTree.nearest_neighbor_query() but slower
def brute_force_nearest_neighbor(points, query_point):
    best_point = None
    best_dist = float('inf')
    for p in points:
        diff = imap(float.__sub__, p, query_point)
        dist = sum(map(lambda x: x*x, diff)) 
        if(dist < best_dist):
            best_dist = dist
            best_point = p
    return best_point, best_dist

#A sipmle class for testing the KDTree
class TestPoint:
    region_id = 0
    def __init__(self, x, y):
        self.location = [x,y]
    def __getitem__(self, x):
        return self.location[x]
    def __len__(self):
        return len(self.location)



#Generates a bunch of random TestPoints for testing
def generate_random_points(num_points):
    points = []
    for i in range(num_points):
        points.append(TestPoint(random(), random()))
    return points
        

#Simple test code.  Generates a bunch of random samples, builds a kd tree, then
#queries with a bunch of other points.  Compares results against brute force method
#Finally, it teests the KDTree.get_leaf() method by comparing leaves of neighbor nodes
#They should be the same most of the time (unless leaf_size is very small)
if __name__ == "__main__":
    from random import random
    print("Generating points")
    train_points = generate_random_points(10000)
    print("Growing tree")
    kdtree = KDTree(train_points, leaf_size=100)
    
    test_points = generate_random_points(100)
    
    print("Querying (fast way and slow way)")
    num_mistakes = 0
    for t in test_points:
        best_point, best_squared_dist = kdtree.nearest_neighbor_query(t)
        best_point2, best_squared_dist2 = brute_force_nearest_neighbor(train_points, t)
        if(best_point != best_point2):
            num_mistakes += 1
    print "Number of mistakes : " + str(num_mistakes)
    
    test_points = generate_random_points(1000)
    print("Checking regions")
    matches = 0
    for t in test_points:
        leaf1 = kdtree.get_leaf(t)
        best_point, best_squared_dist = kdtree.nearest_neighbor_query(t)
        leaf2 = kdtree.get_leaf(best_point)
        if(leaf1==leaf2):
            matches += 1
    
    print("Query point and neighbor in same region (" + str(matches) + " / " + str(len(test_points)) + ")")
        
    
        
            
            
            