import Queue
from AbortedDijkstra import abortedDijkstra
from datetime import datetime

import numpy as np


# An implementation of multi-origin dijkstra
class DijkstrasAlgorithm:
    # Gives out sequential id numbers to the boundary nodes in this region
    #These values are used to index the node.time_from_boundary_node array
    @staticmethod
    def init_boundary_node_ids(list_of_boundary_nodes):
        i = 0
        sorted_boundary_nodes = sorted(list_of_boundary_nodes, key=lambda x: x.id)
        for node in sorted_boundary_nodes:
            node.boundary_node_id = i
            i += 1

    # Sets up lists of "INF" for each nodes, excluding boundary nodes
    @staticmethod
    def initialize_nodes(boundary_nodes_list, grid_of_nodes):
        
        for tmp_node in boundary_nodes_list:
            break
        this_region_id = tmp_node.region_id
        
        for column in grid_of_nodes:
            for region in column:
                for node in region.nodes:
                    # Each node needs a distance from each boundary node
                    # all starting at infinity
                    node.time_from_boundary_node = np.repeat(float("INF"), len(boundary_nodes_list))
                    
                    
                    if node.is_boundary_node and node.region_id==this_region_id:
                        #All boundary nodes in this region are 0 distance away from themselves
                        index = node.boundary_node_id
                        node.time_from_boundary_node[index] = 0
                    
                    # Store a deep copy snapshot of time_from_boundary_node for
                    # future comparison
                    node.time_snapshot = np.copy(node.time_from_boundary_node)
                    node.arc_flag_paths = [None] * len(boundary_nodes_list)
    
    #Computes the shortest path between all pairs of boundary nodes
    #If this id done before the main dijkstra() search, performance should be much better
    @staticmethod
    def initialize_boundary_nodes(boundary_nodes_list, grid_of_nodes, this_region_only):
        
        visited_nodes = set()
        for boundary_node in boundary_nodes_list:
            index = boundary_node.boundary_node_id
            partial_visited_nodes, num_expanded, max_pq_Size = abortedDijkstra(
                                boundary_node, index, boundary_nodes_list, this_region_only)
            visited_nodes.update(partial_visited_nodes)

    
        #Update the snapshots of the boundary nodes        
        for boundary_node in boundary_nodes_list:
            np.copyto(boundary_node.time_snapshot, boundary_node.time_from_boundary_node)
        """
        #reset all of the labels except the boundary nodes in this region
        for column in grid_of_nodes:
            for region in column:
                for node in region.nodes:
                    # Each node needs a distance from each boundary node
                    # all starting at infinity
                    if(node.is_boundary_node and node.region_id==boundary_node.region_id):
                        for boundary_node in boundary_nodes_list:
                            index = boundary_indices[boundary_node]
                            node.was_updated.add(index)
                    else:
                        node.time_from_boundary_node = (
                        [float("INF")] * len(boundary_nodes_list))
        """
        return visited_nodes


    # Keeps a dictionary of how far away a given node is away from a given
    # boundary node
    @staticmethod
    def distance_dictionary(boundary_indices, boundary_nodes, grid_of_nodes):
        dist_dict = dict()
        for boundnode in boundary_nodes:
            index = boundary_indices[boundnode]
            for column in grid_of_nodes:
                for region in column:
                    for node in region.nodes:
                        dist_dict[(boundnode.id, node.id)] = (
                            node.time_from_boundary_node[index])
        return dist_dict

    # Every node in array nodes gets reset so it has no distance from anything,
    # no time from anything, and came from nothing (used to reset after making
    # the path)
    @staticmethod
    def reset_nodes(arr_nodes):
        for node in arr_nodes:
            if node is not None:
                node.came_from = None
                node.best_time = float("INF")
                node.arc_flag_paths = []
                node.time_from_boundary_nodes = []

    # Basically creates a tree rooted at the boundary node where every edge in
    # the tree is an arcflag
    @staticmethod
    def dijkstra(boundary_nodes, grid_of_nodes, warm_start):
        start_time = datetime.now()
        
        max_queue_size = 0  # debug
        expansion_count = 0  # debug
        
        #Assign sequential IDs to the boundary nodes of this region
        DijkstrasAlgorithm.init_boundary_node_ids(boundary_nodes)
        
        #Look at the first boundary node to get the region_id
        for boundary_node in boundary_nodes:
                this_region_id = boundary_node.region_id
                break


        print("initializing")
        # Gives each node a distance from the boundary nodes, which are
        # initially either INF(infinity) or 0
        DijkstrasAlgorithm.initialize_nodes(boundary_nodes, grid_of_nodes)
        
        #Compute pairwise distances between boundary nodes, so only good information is propagated
        if(warm_start):
            print("warmstarting")
            touched_nodes = DijkstrasAlgorithm.initialize_boundary_nodes(boundary_nodes, grid_of_nodes, False)
        else:
            touched_nodes = boundary_nodes


        print("Running Dijkstra with " + str(len(boundary_nodes)) + " boundary nodes.")
        # Nodes we intend to search (somehow connected to graph so far). We
        # treat this as a priority queue: the one that has the potential to be
        # closest (has best distance from the start_node/is closest to the
        # end_node) is treated next
        nodes_to_search = Queue.PriorityQueue()


        for node in touched_nodes:
            if(warm_start==False or node.get_boundary_time_inf_count() == 0):
                nodes_to_search.put((
                            # times updated since it was last expanded
                            node.get_min_boundary_time(),
                            # minimum time from boundary node
                            node.get_min_boundary_time(),
                            # number of infinities in the list
                            node.get_boundary_time_inf_count(),
                            # sum of non infinities in the list
                            node.get_boundary_time_sum(),
                            # the actual node itself
                            node))
        
        counter = 0
        
        #import pdb; pdb.set_trace()
        while not nodes_to_search.empty():
            # Gets the node closest to the end node in the best case
            if (nodes_to_search.qsize() > max_queue_size):
                max_queue_size = nodes_to_search.qsize()
            if counter % 10000 == 0:
                print str(datetime.now() - start_time) + "   " + str(nodes_to_search.qsize())
            counter += 1

            queue_item = nodes_to_search.get()
            old_dom_value, old_min_time, old_inf_count, old_sum = queue_item[0:4]
            curr_node = queue_item[4]
         
            # Skip if the item in queue is out-dated
            if (old_min_time > curr_node.get_min_boundary_time() or
                    old_inf_count > curr_node.get_boundary_time_inf_count() or
                    old_sum < curr_node.get_boundary_time_sum()):
                continue
            
            if(curr_node.is_boundary_node and curr_node.region_id==this_region_id):
                print "****"+ "(" + str(expansion_count) + " / " + str(counter) + ") BoundaryNode(" + str(curr_node.boundary_node_id) + ") : " + str(old_dom_value)

            # Overwrite the snapshot with a copy of the current label
            np.copyto(curr_node.time_snapshot, curr_node.time_from_boundary_node)
                    
            # expansion of curr_node starts here
            expansion_count += 1
            for connected_node in curr_node.backwards_connections:
                
                
                if connected_node.time_connections[curr_node] <= 0:
                    continue
                
                #The proposed distances from all boundary nodes if you go through curr_node
                #i.e. curr_node's distances from the boundary nodes + the length of this link
                proposed_label = curr_node.time_from_boundary_node + connected_node.time_connections[curr_node]
                
                #Only shorter paths are accepted - perform the element-wise min against current values
                proposed_label = np.minimum(proposed_label, connected_node.time_from_boundary_node)
                
                #If there were any changes, copy and note them
                has_updates = False
                if(not np.array_equal(proposed_label, connected_node.time_from_boundary_node)):
                    has_updates=True
                    np.copyto(connected_node.time_from_boundary_node, proposed_label)
                    #TODO: set connected_node.arc_flag_paths
                

                if has_updates and connected_node.get_domination_value() > 0:
                    nodes_to_search.put((
                        # times updated since it was last expanded
                        connected_node.get_min_boundary_time(),
                        # minimum time from boundary node
                        connected_node.get_min_boundary_time(),
                        # number of infinities in the list
                        connected_node.get_boundary_time_inf_count(),
                        # sum of non infinities in the list
                        connected_node.get_boundary_time_sum(),
                        # the actual node itself
                        connected_node))

        DijkstrasAlgorithm.set_arc_flags(grid_of_nodes)

        print "Max Queue Size:", max_queue_size  # debug
        print "Number of expansions:", expansion_count  # debug

    #Runs a Dijkstra search independently for each boundary node.
    @staticmethod
    def independentDijkstra(boundary_nodes, grid_of_nodes):
         # Assign each boundary node an i for distance
        DijkstrasAlgorithm.init_boundary_node_ids(boundary_nodes)
        
        print("initializing")
        # Gives each node a distance from the boundary nodes, which are
        # initially either INF(infinity) or 0
        DijkstrasAlgorithm.initialize_nodes(boundary_nodes, grid_of_nodes)
        
        for boundary_node in boundary_nodes:
            print "processing boundary node " + str(boundary_node.boundary_node_id)
            tmp, num_expanded, max_pq_size = abortedDijkstra(boundary_node, None)
            print "expanded_nodes: " + str(num_expanded) + " , max_pq_size: " + str(max_pq_size)
        
        


    # Given where the nodes came from, rebuilds the path that was taken to the
    # final node
    @staticmethod
    def set_arc_flags(grid_of_nodes):
        for column in grid_of_nodes:
            for grid_region in column:
                for node in grid_region.nodes:
                    for connection in node.arc_flag_paths:
                        if connection is not None:
                            node.is_arc_flags[connection] = True
                DijkstrasAlgorithm.reset_nodes(grid_region.nodes)
