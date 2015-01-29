# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 16:00:30 2015

@author: brian
"""
from routing.Map import Map
from datetime import datetime
import csv

def dfs(start_node, forward=True, visited_set = set()):
    stack = [start_node]
    visited_set.add(start_node)
    finished_nodes = []
    
    i = 0
    while(len(stack) > 0):
        i += 1

        node = stack[-1]
        
        if(forward):
            links = node.forward_links
        else:
            links = node.backward_links
        
        finished = True
        for link in links:
            if(forward):
                neighbor = link.connecting_node
            else:
                neighbor = link.origin_node
            
            if(neighbor not in visited_set):
                stack.append(neighbor)
                visited_set.add(neighbor)
                finished = False
        
        if(finished):
            _ = stack.pop()
            finished_nodes.append(node)
    
    return finished_nodes




def kosaraju(nodes):
    already_assigned_nodes = set()
    scc_list = []
    
    for starting_node in nodes:
        if(starting_node not in already_assigned_nodes):
            ordered_nodes = dfs(starting_node)
        
            for node in ordered_nodes:
                if node not in already_assigned_nodes:
                    scc = dfs(node, forward=False, visited_set = set(already_assigned_nodes))
                    already_assigned_nodes.update(scc)
                    scc_list.append(scc)
    
    return scc_list

    
def test_kosaraju():
    print("Loading map...")
    m = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Num nodes : " + str(len(m.nodes)))
    print("running kosaraju")
    d1 = datetime.now()
    sccs = kosaraju(m.nodes)
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
    
    