# -*- coding: utf-8 -*-
"""
Created on Fri Mar 27 22:25:43 2015

@author: Brian Donovan (briandonovan100@gmail.com)
"""
from os import system
from routing.Map import Map
from scipy.sparse import dok_matrix, csr_matrix
from scipy.sparse.linalg import lobpcg
from sklearn.cluster import k_means

import numpy as np

import csv
from collections import defaultdict


# Runs the KaHIP program kaffpaE in order to cluster the nodes of the graph, according
# to a balanced min cut criteria.  Assumes that the KaHIP programs have already
# been properly built and are located in a folder called KaHIP.  The results of
# the clustering will be saved into the node.region_id field for each node of
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
            road_map.nodes[i].region_id = int(line)
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
            w.writerow([num_clusters, imbalance, node.lat, node.long, node.region_id])
            


# Uses an R script to plot a visual representation of the clustered map.
# Params:
    # cluster_filename - the file where cluster data is stored.  This is the file
        # produced by output_clusters()
    # output_filename - a PDF file where the results will be saved
def plot_map(cluster_filename, output_filename, link_filename='[IGNORE]'):
    # Build command to execute R plotting script, and execute it
    cmd = "Rscript routing/plot_clusters.R %s %s %s" % (
        cluster_filename, link_filename, output_filename)
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


def plot_test():
    print("Loading")
    road_map = Map("nyc_map4/nodes_no_nj_imb20_k10.csv", "nyc_map4/links_no_nj_imb20_k10.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Outputting")    
    output_clusters(road_map, 10, 20, 'tmp_cluster.csv')
    
    print("Drawing")
    plot_map('tmp_cluster.csv', 'graph_clusters.pdf', link_filename='nyc_map4/links_no_nj_imb20_k10.csv')



#  Identifies the Western-most cluster.  This is NJ
def find_new_jersey_region(road_map):
    # We will do this by computing the average longitude in each cluster
    s_lon = defaultdict(int)
    n_lon = defaultdict(int)
    for node in road_map.nodes:
        s_lon[node.region_id] += node.long
        n_lon[node.region_id] += 1
    
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
    nj_nodes = [node for node in road_map.nodes if node.region_id==nj_region]
    road_map.delete_nodes(nj_nodes)
    
    # Save 'after' map
    print("Outputting")
    output_clusters(road_map, 4, 5, 'tmp_cluster.csv')
    plot_map('tmp_cluster.csv', 'without_new_jersey.pdf')
    
    print("Saving")
    road_map.save_as_csv('nyc_map4/nodes_no_nj.csv', 'nyc_map4/links_no_nj.csv')
    







def build_adjacency_matrix(road_map):
    # First, re-index nodes from 0 to N-1
    n = len(road_map.nodes)
    new_node_ids = {}
    for i in range(n):
        new_node_ids[road_map.nodes[i].node_id] = i
    
    
    
    
    # Next, produce affinity matrix (which is a sparse matrix)
    a = dok_matrix((n,n)) #Sparse matrix format
    for i in range(n):
        if(i%1000 ==0):
            print(i)
        
        node = road_map.nodes[i]
        for link in node.forward_links:
            neighbor = link.connecting_node
            j = new_node_ids[neighbor.node_id]
          
            if(link.road_class in ("motorway", "motorway_link")):
                a[i,j] = .01
                a[j,i] = .01
            else:
                a[i,j] = 1
                a[j,i] = 1
        a[i,i] = 1
            
    a = csr_matrix(a)
    return a
    




def build_laplacian(a_matrix, normalize=False):
    print("Normalize? %s" % str(normalize))
    (n, _) = a_matrix.shape
    d_matrix = dok_matrix((n,n))
    node_degrees = a_matrix.sum(axis=0)
    
    for i in xrange(n):
        d_matrix[i,i] = node_degrees[0,i]
    
    laplacian = csr_matrix(d_matrix - a_matrix)
    
    if(normalize):
        sqrt_diag = csr_matrix((n,n))
        for i in xrange(n):
            sqrt_diag[i,i] = 1.0 / np.sqrt(d_matrix[i,i])
        
        laplacian = sqrt_diag * laplacian * sqrt_diag
    
    
    return laplacian


def sorted_eig(a):
    eigenValues,eigenVectors = np.linalg.eig(a)

    idx = eigenValues.argsort()   
    eigenValues = eigenValues[idx]
    eigenVectors = eigenVectors[:,idx]
    
    return eigenValues, eigenVectors


def spectral_clustering(road_map=None, a=None, use_ncut=False, num_clusters=2):
    print("Building adjacency matrix")
    if(a==None):
        a = build_adjacency_matrix(road_map)
    
    print("Computing laplacian")
    l = build_laplacian(a, normalize=use_ncut)
    
    print("Spectral embedding")
    #e_vals, e_vects = eigsh(l, k=num_clusters, which='SM', tol=0.01, sigma=2.01)
    X = np.random.rand(l.shape[0], num_clusters+1)
    e_vals, e_vects = lobpcg(l, X, tol=1e-15,
                                            largest=False, maxiter=2000)    
    
    
    
    embedded_data = e_vects[:,1:]
    
    print e_vals
    
    

    print("Clustering")
    centroid, label, intertia = k_means(embedded_data, num_clusters)
    
    for i in xrange(len(label)):
        road_map.nodes[i].region_id = label[i]









# Runs the clustering for multiple values of K and imbalance, and plots all of the results
# in one big PDF
def run_many_tests():
    print("Loading")
    road_map = Map("nyc_map4/nodes_no_nj.csv", "nyc_map4/links_no_nj.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Saving")
    road_map.save_as_metis('nyc_map4/nyc_no_nj.metis')

    print("Clustering")

    append = False
    #imb_vals = [10,15,20,25]
    #k_vals = [2,3,4,5,6,7,8,9,10,15,20,30,40,50,100]
    
    imb_vals = [20]
    k_vals = [1,2,3,4,5,6,7,8,9,10,15,20,25,30,35,40,45,50]
    for imb in imb_vals:        
        for k in k_vals:
            
            print ("imb=%d, k=%d" % (imb,k))
            # Cluster the graph into K clusters with imb% imbalance allowed
            run_KaFFPaE(road_map, graph_filename="nyc_map4/nyc_no_nj.metis", 
                        num_clusters=k, imbalance=imb, time=120, num_cpus=2)
            
            # Output the clusters to the file.
            output_clusters(road_map, k, imb, 'tmp_cluster.csv', append=append)
            # Future clusterings will be appended to the file instead of overwriting
            append=True 
    
    
            print("Saving")
            nodes_fn = 'nyc_map4/nodes_no_nj_imb%d_k%d.csv' % (imb, k)
            links_fn = 'nyc_map4/links_no_nj_imb%d_k%d.csv' % (imb, k)
            road_map.save_as_csv(nodes_fn, links_fn)
            
    # Once the file is produced, plot it
    plot_map('tmp_cluster.csv', 'graph_clusters.pdf')
    
    
# Runs the clustering for multiple values of K and imbalance, and plots all of the results
# in one big PDF
def run_many_tests_spectral():
    print("Loading")
    road_map = Map("nyc_map4/nodes_no_nj.csv", "nyc_map4/links_no_nj.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Saving")
    road_map.save_as_metis('nyc_map4/nyc_no_nj.metis')

    print("Clustering")

    append = False
    #imb_vals = [10,15,20,25]
    #k_vals = [2,3,4,5,6,7,8,9,10,15,20,30,40,50,100]
    

    k_vals = [2,3,4,5,6,7,8,9,10]      
    for k in k_vals:
        
        print ("k=%d" % k)
        # Cluster the graph into K clusters with imb% imbalance allowed
        
        spectral_clustering(road_map=road_map, use_ncut=True, num_clusters=k)

        
        # Output the clusters to the file.
        output_clusters(road_map, k, 0, 'tmp_cluster_ncut.csv', append=append)
        # Future clusterings will be appended to the file instead of overwriting
        append=True 


        #print("Saving")
        #nodes_fn = 'nyc_map4/nodes_no_nj_imb%d_k%d.csv' % (imb, k)
        #links_fn = 'nyc_map4/links_no_nj_imb%d_k%d.csv' % (imb, k)
        #road_map.save_as_csv(nodes_fn, links_fn)
            
    # Once the file is produced, plot it
    plot_map('tmp_cluster_ncut.csv', 'n_cut_graph_clusters.pdf')