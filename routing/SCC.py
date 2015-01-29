# -*- coding: utf-8 -*-
"""
Methods for finding the strongly-connected-components of a graph stored in a Map object.
Created on Wed Jan 28 16:00:30 2015

@author: brian
"""
import Map
from datetime import datetime
import csv

# Helper method which performs depth-first search and returns nodes in their expanded order
# Params:
    # start_node - The node to start searching from
    # forward - If True, will search on the forward graph, if False, will search
        # on the backward garph
    # visited_set - A set of nodes which have already been visited.  Nodes in this
    # set will be ignored.  Nodes will be added to this set as they are discovered
# Returns: A list of nodes in the order that they FINISH.  A node is only finished
    # once all of its children in the search tree are finished.  So the start_node
    # will be the last to finish
def dfs(start_node, forward=True, visited_set = set()):

    # The stack of nodes to expand, used for DFS
    stack = [start_node]
    # The start_node has now been visited
    visited_set.add(start_node)
    
    # List of nodes
    finished_nodes = []

    # Iterate until the stack runs out    
    while(len(stack) > 0):

        # Peek at the top node of the stack
        node = stack[-1]
        
        # Decide whether we are going forward or backward
        if(forward):
            links = node.forward_links
        else:
            links = node.backward_links
        
        # This node is only finished if all of its neighbors are finished
        finished = True
        for link in links:
            # Variable 'forward' determines which end of the Link to look at
            if(forward):
                neighbor = link.connecting_node
            else:
                neighbor = link.origin_node
            
            # Neighbor has not been explored yet
            if(neighbor not in visited_set):
                # Mark as visited and add to the stack so it will be explored later
                stack.append(neighbor)
                visited_set.add(neighbor)
                # This node is not done yet because its neighbor still needs to be explored
                finished = False
        
        # Remove the node from the stack if it is finished
        if(finished):
            _ = stack.pop()
            # Add to the output list
            finished_nodes.append(node)
    
    return finished_nodes



# Finds the strongly connected components (SCCs) of a graph, using Kosaraju's Algorithm.
# Parameters:
    # nodes - A list of Node objects, which presumably have Links to each other
# Returns:
    # A list of SCCs, each of which is a list of Nodes
def kosaraju(nodes):
    
    scc_list = []
    
    # Step 1 - determine Node search order.  The first node to search should be in
    # the top of a topological sort of the graph
    discovered_nodes = set()
    ordered_nodes = []
    # Run through all of the Nodes and DFS from them if they haven't been searched yet
    for starting_node in nodes:
        if(starting_node not in discovered_nodes):
            nodes = dfs(starting_node, visited_set=discovered_nodes)
            ordered_nodes += nodes
    # Reverse the list so the top nodes will come first
    ordered_nodes.reverse()
    
    # Step 2 - Find SCCs using the backwards graph.  We will check which Nodes can
    # get back to these top nodes, ignoring the SCCs that have been found so far
    discovered_nodes = set()
    for node in ordered_nodes:
        if node not in discovered_nodes:
            # The DFS returns a strongly connected component
            scc = dfs(node, forward=False, visited_set = set(discovered_nodes))
            
            # But this SCC will be ignored in subsequent calls
            discovered_nodes.update(scc)
            
            # Add the SCC to the output list
            scc_list.append(scc)
    
    return scc_list

    
def test_kosaraju():
    print("Loading map...")
    m = Map.Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Num nodes : " + str(len(m.nodes)))
    print("running kosaraju")
    d1 = datetime.now()
    sccs = kosaraju(m.nodes)
    sccs.sort(key=lambda x: len(x), reverse=True)
    d2 = datetime.now()
    print("Done %s" % str(d2 - d1))
    print("Found %d SCCs.  Sizes:" % len(sccs))
    
    with open("nyc_map4/strongly_connected_components.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["lat","lon","scc_id"])
        i = 0
        for scc in sccs:
            print("--- %d" % len(scc))
            for node in scc:
                writer.writerow([node.lat, node.long, i])
            i += 1

def test_clean_graph():
    print("Loading map...")
    m = Map.Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Num nodes : " + str(len(m.nodes)))
    print("cleaning graph")
    d1 = datetime.now()
    m.remove_extra_sccs()
    d2 = datetime.now()
    print("Done %s" % str(d2 - d1))

    sccs = kosaraju(m.nodes)
    sccs.sort(key=lambda x: len(x), reverse=True)

    

    for scc in sccs:
        print("--- %d" % len(scc))

    