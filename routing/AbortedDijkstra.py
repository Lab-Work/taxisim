# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 16:14:48 2014

@author: Brian Donovan (briandonovan100@gmail.com)
"""

from Queue import PriorityQueue


# A Dijkstra search that aborts when all of the boundary_nodes have been
# expanded
# params:
#    origin_node - the node that the search originates
#    origin_nodeId - see DijkstrasAlgorithm.init_dict()
#    boundary_nodes - nodes at the boundary of the region.  The search stops
#                    when they are all expanded
#    this_region_only - if True, ignore nodes from other regions (WARNING:
#                       shortest path between two boundary nodes may go outside
#                       of region.)
#    on_forward_graph - if True, use the backward_links to expand
# returns:
#    nodes_to_search - the "frontier" of nodes which have been touche
def aborted_dijkstra(origin_node, boundary_nodes, this_region_only=False,
                     on_forward_graph=True):
    # maintain set of boundary  nodes that have been visited by this search
    visited_boundary_nodes = set()
    visited_nodes = set()
    i = origin_node.boundary_node_id

    # Initialize Dijkstra queue with the origin node
    nodes_to_search = PriorityQueue()
    nodes_to_search.put((0, origin_node))

    expanded_count = 0
    max_pq_size = 0

    while(not nodes_to_search.empty()):
        # Get the nearest node from the priority queue
        max_pq_size = max(nodes_to_search.qsize(), max_pq_size)
        (_, node) = nodes_to_search.get()
        expanded_count += 1

        if boundary_nodes is not None:
            visited_nodes.add(node)
        # If this is a boundary node for this region, mark it as visited
        if(boundary_nodes is not None and node.is_boundary_node and
           node.region_id == origin_node.region_id):
            visited_boundary_nodes.add(node)
            # If we have now visited all boundary nodes, stop early
            if len(visited_boundary_nodes) == len(boundary_nodes):
                break
        connecting_links = None
        if on_forward_graph:
            connecting_links = node.backward_links
        else:
            connecting_links = node.forward_links
        # Propagate to neighbors on the forward graph using the backward links
        for connecting_link in connecting_links:
            neighbor = None
            if on_forward_graph:
                neighbor = connecting_link.origin_node
            else:
                neighbor = connecting_link.connecting_node
            # if this_region_only is set, then skip nodes from other regions
            if(this_region_only and
               neighbor.region_id != origin_node.region_id):
                continue
            time_from_boundary_node = None
            neighbor_time = None
            if on_forward_graph:
                time_from_boundary_node = node.forward_boundary_time
                neighbor_time = neighbor.forward_boundary_time
            else:
                time_from_boundary_node = node.backward_boundary_time
                neighbor_time = neighbor.backward_boundary_time
            # Compute the distance if we were to travel to the neighbor from
            # the current node
            proposed_distance = (time_from_boundary_node[i] +
                                 connecting_link.time)
            # If this is better than the current best path to the neighbor,
            # update it (relaxation)
            if(proposed_distance < neighbor_time[i]):
                neighbor_time[i] = proposed_distance
                # since the distance was updated, this node needs to be
                # re-added to the PQ
                nodes_to_search.put((proposed_distance, neighbor))

    # Now, all origin nodes (and some other nodes) all know their distance from
    # the given origin_node
    return visited_nodes, expanded_count, max_pq_size
