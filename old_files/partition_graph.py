#from sklearn.cluster import SpectralClustering
from sklearn.utils.arpack import eigsh
from sklearn.cluster import k_means
from scipy.sparse import dok_matrix, csr_matrix
from scipy.sparse.linalg import lobpcg
from routing.Map import Map
from datetime import datetime
from math import exp

from routing.AbortedDijkstra import find_nearest_neighbors, reset_all_node_costs
import csv

import numpy as np


def build_adjacency_matrix(road_map):
    # First, re-index nodes from 0 to N-1
    n = len(road_map.nodes)
    new_node_ids = {}
    for i in range(n):
        new_node_ids[road_map.nodes[i].node_id] = i
    
    
    reset_all_node_costs(road_map)    
    
    
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
    




def build_affinity_matrix(road_map, num_neighbors, sigma):
    # First, re-index nodes from 0 to N-1
    n = len(road_map.nodes)
    new_node_ids = {}
    for i in range(n):
        new_node_ids[road_map.nodes[i].node_id] = i
    
    
    reset_all_node_costs(road_map)    
    
    
    # Next, produce affinity matrix (which is a sparse matrix)
    a = dok_matrix((n,n)) #Sparse matrix format
    for i in range(n):
        if(i%1000 ==0):
            print(i)
        node = road_map.nodes[i]
        neighbor_costs = find_nearest_neighbors(node, num_neighbors, True)
        for neighbor in neighbor_costs:
            cost = neighbor_costs[neighbor]
            affinity = exp(-(cost/sigma)**2)
            j = new_node_ids[neighbor.node_id]
            
            a[i,j] = max(a[i,j], affinity)
            a[j,i] = max(a[j,i], affinity)
            #a[i,j] = 1
            #[j,i] = 1            
            
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
    
    return label






def partition(road_map, num_clusters):
    # First, re-index nodes from 0 to N-1
    n = len(road_map.nodes)
    new_node_ids = {}
    for i in range(n):
        new_node_ids[road_map.nodes[i].node_id] = i
    
    
    #a = build_affinity_matrix(road_map, 30, 20)
    a = build_adjacency_matrix(road_map)
    print(a.shape)

    s = SpectralClustering(affinity='precomputed', n_clusters=num_clusters,
                           norm_laplacian=False, eigen_solver='arpack')
    #s = SpectralClustering(affinity='precomputed', n_clusters=num_clusters)
    return s.fit_predict(a)

def test_cluster():
    #a = np.matrix('1 1 1 0 0 0; 1 1 1 0 0 0; 1 1 1 1 0 0 ; 0 0 1 1 1 1; 0 0 0 1 1 1; 0 0 0 1 1 1')
    
    #spectral_clustering(a=a, num_clusters=2)
    
    #return
    
    print("Loading graph")
    #bbox = (-74.05, 40.8, -73.85, 40.7)
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print("Partitioning")
    
    d1 = datetime.now()
    prev_d = d1
    for n in range(2,11):
        #labels = partition(road_map, 3)
        labels = spectral_clustering(road_map=road_map, num_clusters=n, use_ncut=False)
        
        filename = 'weight_clusters_%d.csv' % n
        with open(filename, 'w') as f:
            w = csv.writer(f)
            w.writerow(['lat','lon','region'])
            for i in xrange(len(road_map.nodes)):
                w.writerow([road_map.nodes[i].lat, road_map.nodes[i].long, labels[i]])
        
        d = datetime.now()
        print(str(d - prev_d))
        prev_d = d
        
        