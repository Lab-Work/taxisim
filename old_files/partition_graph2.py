# -*- coding: utf-8 -*-
"""
Created on Thu Mar 26 16:58:02 2015

@author: Brian Donovan (briandonovan100@gmail.com)
"""
from igraph import Graph
from random import shuffle
import csv

from routing.Map import Map


def convert_to_igraph(road_map):
    # First, re-index nodes from 0 to N-1

    shuffle(road_map.nodes)
    
    n = len(road_map.nodes)
    new_node_ids = {}
    for i in xrange(n):
        new_node_ids[road_map.nodes[i].node_id] = i
    
    # Now, create a Graph object with the correct number of nodes
    graph = Graph(n, directed=False)
    
    """
    # Add the correct links
    for i in xrange(n):
        if(i%1000==0):
            print i
        for link in road_map.nodes[i].forward_links:
            j = new_node_ids[link.connecting_node.node_id]
            graph.add_edge(i,j)
    """
    edge_set = set()
    
    for i in xrange(n):
        for link in road_map.nodes[i].forward_links:
            j = new_node_ids[link.connecting_node.node_id]
            
            x = min(i,j)
            y = max(i,j)
            edge_set.add((x,y))
    
    graph.add_edges(list(edge_set))
    
    return graph

def cluster_map(road_map):
    print("Preprocessing")
    graph = convert_to_igraph(road_map)
    
    print("Clustering")
    hierarchy = graph.community_fastgreedy()
    
    print("Outputting")
    
    
    filename = 'modular_clusters.csv'
    with open(filename, 'w') as f:
        w = csv.writer(f)
        w.writerow(['k', 'lat','lon','region'])
        for k in xrange(1,21):
            
            clustering = hierarchy.as_clustering(n=k)
            print("k=%d, mod=%f" % (k, clustering.modularity))
            labels = clustering.membership
            
            
            for i in xrange(len(road_map.nodes)):
                w.writerow([k, road_map.nodes[i].lat, road_map.nodes[i].long, labels[i]])

    

def test_cluster():
    #a = np.matrix('1 1 1 0 0 0; 1 1 1 0 0 0; 1 1 1 1 0 0 ; 0 0 1 1 1 1; 0 0 0 1 1 1; 0 0 0 1 1 1')
    
    #spectral_clustering(a=a, num_clusters=2)
    
    #return
    
    print("Loading graph")
    #bbox = (-74.05, 40.8, -73.85, 40.7)
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    
    cluster_map(road_map)
    
    