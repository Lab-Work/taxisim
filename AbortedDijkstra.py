# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 16:14:48 2014

@author: Brian Donovan (briandonovan100@gmail.com)
"""

from Queue import PriorityQueue

#A Dijkstra search that aborts when all of the boundaryNodes have been expanded
#params:
    #originNode - the node that the search originates
    #originNodeId - see DijkstrasAlgorithm.init_dict()
    #boundaryNodes - nodes at the boundary of the region.  The search stops when they are all expanded
    #this_region_only - if True, ignore nodes from other regions (WARNING: shortest path between two boundary nodes may go outside of region.)
#returns:
    #nodes_to_search - the "frontier" of nodes which have been touche 
def abortedDijkstra(originNode, originNodeId, boundaryNodes, this_region_only=False):
    #maintain set of boundary  nodes that have been visited by this search
    visited_boundary_nodes = set()
    visited_nodes = set()
    i = originNodeId
    
    #Initialize Dijkstra queue with the origin node
    nodes_to_search = PriorityQueue()
    nodes_to_search.put((0, originNode))
    
    expanded_count = 0
    max_pq_size = 0
    
    while(not nodes_to_search.empty()):
        #Get the nearest node from the priority queue
        max_pq_size = max(nodes_to_search.qsize(), max_pq_size)
        (dist, node) = nodes_to_search.get()
        expanded_count+=1
        
        visited_nodes.add(node)
        
        #If this is a boundary node for this region, mark it as visited
        if(boundaryNodes!= None and node.is_boundary_node and node.region_id == originNode.region_id):        
            visited_boundary_nodes.add(node)
            #If we have now visited all bondary nodes, stop early
            if(len(visited_boundary_nodes) == len(boundaryNodes)):
                break
            
        
        #Propagate to neighbors
        for neighbor in node.backwards_connections:
            #if this_region_only is set, then skip nodes from other regions
            if(this_region_only and neighbor.region_id != originNode.region_id):
                continue
            #Compute the distance if we were to travel to the neighbor from the current node
            proposed_distance = node.time_from_boundary_node[i] + neighbor.time_connections[node]
            
            #If this is better than the current best path to the neighbor, update it (relaxation)
            if(proposed_distance < neighbor.time_from_boundary_node[i]):
                neighbor.time_from_boundary_node[i] = proposed_distance
                neighbor.was_updated.add(i)
                #since the distance was updated, this node needs to be re-added to the PQ
                nodes_to_search.put((proposed_distance, neighbor))
                
    
    #Now, all origin nodes (and some other nodes) all know their distance from the given originNode
    return visited_nodes, expanded_count, max_pq_size


    
    
    
