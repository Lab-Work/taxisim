# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 22:25:43 2015

@author: Brian Donovan (briandonovan100@gmail.com)
"""
from os import system
from routing.Map import Map

import csv
from collections import defaultdict


# Runs the KaHIP program kaffpaE in order to cluster the nodes of the graph, according
# to a balanced min cut criteria.  Assumes that the KaHIP programs have already
# been properly built and are located in a folder called KaHIP.  The results of
# the clustering will be saved into the node.cluster_id field for each node of
# the graph.
# Params:
    # road_map - a Map object to be clustered
    # graph_filename - an optional filename which contains the road graph in METIS
        # format.  If none is given, it will be generated from the road_map
    # num_clusters - the number of desired clusters, will be passed to kaffpaE
    # imbalance - The percentage of imbalance allowed between cluster sizes,
        # which will be passed to kaffpaE
    # time - The cutoff time for the algorithm, will be passed to kaffpaE
    # num_cpus - The number of CPUs available for kaffpaE to use
def run_KaFFPaE(road_map, graph_filename=None, num_clusters=2, imbalance=10, 
                time=60, num_cpus=2):
    
    # If no graph file is supplied, then build a default one from the graph
    if(graph_filename==None):
        graph_filename = 'tmp_graph.metis'
        road_map.save_as_metis(graph_filename)
    
    # Build the command to run the kaffpE program
    cmd="mpirun -n %d KaHIP/deploy/kaffpaE %s --k %d --time_limit=%d --imbalance=%d --output_filename=%s > /dev/null" % (
        num_cpus, graph_filename, num_clusters, time, imbalance, "tmp_clusters")
    # Execute the command and wait for results
    system(cmd)
    system('sync') # make sure the file is flushed to disk before we try to read it
    
    # Now read the output and assign region IDs to the nodes
    # Nodes in the file will have the same order as nodes in the graph
    with open("tmp_clusters", "r") as f:
        i = 0
        for line in f:
            road_map.nodes[i].cluster_id = int(line)
            i += 1
    

# Outputs the nodes' coordinates and clustering info into a CSV file, which can
# be examined or plotted later.
# Params:
    # road_map - the clustered road map.  run_KaFFPaE() should have already been
        # executed on this map
        # 
def output_clusters(road_map, num_clusters, imbalance, filename, append=False):
    if(append):
        mode='a'
    else:
        mode = 'w'
    
    with open(filename, mode) as f:
        w = csv.writer(f)
        
        if(not append):
            w.writerow(['k', 'imbalance', 'lat', 'lon', 'region'])
        
        for node in road_map.nodes:
            w.writerow([num_clusters, imbalance, node.lat, node.long, node.cluster_id])
            


# Uses an R script to plot a visual representation of the clustered map.
# Params:
    # cluster_filename - the file where cluster data is stored.  This is the file
        # produced by output_clusters()
    # output_filename - a PDF file where the results will be saved
def plot_map(cluster_filename, output_filename):
    # Build command to execute R plotting script, and execute it
    cmd = "Rscript routing/plot_clusters.R %s %s" % (
        cluster_filename, output_filename)
    system(cmd)


# Runs the clustering and plots the results
def simple_test():
    print("Loading")
    road_map = Map("nyc_map4/nodes_no_nj.csv", "nyc_map4/links_no_nj.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Saving")
    road_map.save_as_metis('nyc_map4/nyc_no_nj.metis')

    print("Clustering")
    run_KaFFPaE(road_map, graph_filename="nyc_map4/nyc_no_nj.metis", time=10, imbalance=5,
                num_clusters=4)
    
    output_clusters(road_map, 4, 5, 'tmp_cluster.csv')
    
    plot_map('tmp_cluster.csv', 'graph_clusters.pdf')
    
    return road_map


#  Identifies the Western-most cluster.  This is NJ
def find_new_jersey_region(road_map):
    # We will do this by computing the average longitude in each cluster
    s_lon = defaultdict(int)
    n_lon = defaultdict(int)
    for node in road_map.nodes:
        s_lon[node.cluster_id] += node.long
        n_lon[node.cluster_id] += 1
    
    best_region = -1
    best_lon = float('inf')
    for region_id in s_lon:
        avg_lon = s_lon[region_id] / n_lon[region_id]
        if(avg_lon < best_lon):
            best_lon = avg_lon
            best_region = region_id
    
    return best_region



def delete_new_jersey():
    print("Loading")
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Saving")
    road_map.save_as_metis('nyc_map4/nyc.metis')

    print("Clustering")
    run_KaFFPaE(road_map, graph_filename="nyc_map4/nyc.metis", time=60, imbalance=25,
                num_clusters=4)
    
    # save 'before' map
    print("Outputting")
    output_clusters(road_map, 4, 5, 'tmp_cluster.csv')
    plot_map('tmp_cluster.csv', 'with_new_jersey.pdf')
    
    print("Deleting NJ")
    # Identify nodes that are in NJ and delete them
    nj_region = find_new_jersey_region(road_map)
    print ("--Deleting region %d" % nj_region)
    nj_nodes = [node for node in road_map.nodes if node.cluster_id==nj_region]
    road_map.delete_nodes(nj_nodes)
    
    # Save 'after' map
    print("Outputting")
    output_clusters(road_map, 4, 5, 'tmp_cluster.csv')
    plot_map('tmp_cluster.csv', 'without_new_jersey.pdf')
    
    print("Saving")
    road_map.save_as_csv('nyc_map4/nodes_no_nj.csv', 'nyc_map4/links_no_nj.csv')
    
    
    
    
    
    



# Runs the clustering for multiple values of K and imbalance, and plots all of the results
# in one big PDF
def run_many_tests():
    print("Loading")
    road_map = Map("nyc_map4/nodes_no_nj.csv", "nyc_map4/links_no_nj.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Saving")
    road_map.save_as_metis('nyc_map4/nyc_no_nj.metis')

    print("Clustering")

    append = False
    for imb in [10,15,20,25]:        
        for k in [2,3,4,5,6,7,8,9,10,15,20,30,40,50,100]:
            
            print ("imb=%d, k=%d" % (imb,k))
            # Cluster the graph into K clusters with imb% imbalance allowed
            run_KaFFPaE(road_map, graph_filename="nyc_map4/nyc_no_nj.metis", 
                        num_clusters=k, imbalance=imb, time=60, num_cpus=8)
            
            # Output the clusters to the file.
            output_clusters(road_map, k, imb, 'tmp_cluster.csv', append=append)
            # Future clusterings will be appended to the file instead of overwriting
            append=True 
    
    # Once the file is produced, plot it
    plot_map('tmp_cluster.csv', 'graph_clusters.pdf')
    
    
    