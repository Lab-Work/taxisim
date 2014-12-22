import csv
from Link import Link
# from Grid import set_up_grid
import numpy as np
from math import sqrt

# TODO: REMOVE THE DUPLICATE STUFF TAKING INTO ACCOUNT NONES


def approx_distance(lat1, long1, lat2, long2):
    diff_lat = float(lat1) - float(lat2)
    diff_long = float(long1) - float(long2)
    # meters per degree latitude
    # an approximation based off our latitude and longitude
    lat_miles = diff_lat * 111194.86461
    # meters per degree longitude
    # an approximation  based off our latitude and longitude
    long_miles = diff_long * 84253.1418965
    return sqrt(lat_miles * lat_miles + long_miles * long_miles)


# A vertex in our map
# (edge class not used -> simply used lists within the node)
class Node:

    def __init__(self, begin_node_id, latitude, longitude, region):
        self.node_id = int(begin_node_id)
        self.lat = float(latitude)
        self.long = float(longitude)

        # Convert lat and lon to coordinates in meters (we are assumming that
        # NYC is flat)
        self.location = (self.lat * 111194.86461, self.long * 84253.1418965)
        self.region = int(region)

        # Used for DFS
        self.discovered = False

        # These are nodes that are connected by edges that start at the current
        # node and their weights
        self.forward_links = []
        self.backward_links = []
        self.forward_link_ids = []
        self.backward_link_ids = []

        self.is_forward_arc_flags = {}
        self.is_backward_arc_flags = {}

        ######################################################
        #  Used in multiple dijkstra arcflag precomputation  #
        ######################################################

        # Tells if the node is a boundary node
        self.is_boundary_node = False

        # Uniquely indexes the boundary nodes in each region
        # This index refers to a slot in time_from_boundary_node
        self.boundary_node_id = -1

        # During the dijkstra algorithm, give a set of which indices were
        # updated
        # self.was_updated = set()

        # For multi-origin dijkstra, storing the time from each boundary node
        self.forward_boundary_time = np.array([])
        self.backward_boundary_time = np.array([])

        # A snapshot of the time_from_boundary_node from the last expansion
        self.time_snapshot = np.array([])

        # For each boundary node path, shows where this particular node came
        # from - used in ArcFlags Preprocessing
        self.forward_predecessors = np.array([])
        self.backward_predecessors = np.array([])

        ######################################################
        #  Used at query time                                #
        ######################################################

        self.reset()

        # Checks if the node is currently in the queue (won't add otherwise)
        # self.in_queue = False

        # The number of times this node has been updated since its last
        # expansion
        self.update_count = 0

        # Identifies which region this node belongs to
        self.region_id = (None, None)

    # Used for the KD-tree - the node can be used as an array-like object
    def __getitem__(self, x):
        return self.location[x]

    # Used for the KD-Tree - the node can be used as an array-like object
    def __len__(self):
        return 2

    def reset(self):
        self.forward_predecessor_link = None  # For the forward search
        self.backward_predecessor_link = None  # For the backward search

        # Shows how far this node is from the origin and destination
        # Time from the origin (forward search)
        self.forward_time = float('Inf')
        # Time to the destination (backward search)
        self.backward_time = float('Inf')

        self.was_forward_expanded = False
        self.was_backward_expanded = False

    def approx_dist_to(self, other_node):
        return approx_distance(
            self.lat,
            self.long,
            other_node.lat,
            other_node.long)

    # Given an node_id, gives its weight
    def add_connecting_node(self, node_id, end_node_id, weight, speed, time):
        self.forward_links.append(Link(node_id, end_node_id, weight, speed,
                                       time))

    def set_arc_flags(self, node_id, hex_string):
        # DEPRECATED!
        new_list = hex_deconverter(hex_string)
        self.is_forward_arc_flags[node_id] = new_list
        self.is_backward_arc_flags[node_id] = new_list

    def get_boundary_time_inf_count(self, on_forward_graph):
        if on_forward_graph:
            return np.sum(self.forward_boundary_time == float('inf'))
        else:
            return np.sum(self.backward_boundary_time == float('inf'))

    # Compare time_from_boundary_node with the snapshot from its last expansion
    def get_domination_value(self, on_forward_graph):
        if on_forward_graph:
            return np.sum(self.forward_boundary_time != self.time_snapshot)
        else:
            return np.sum(self.backward_boundary_time != self.time_snapshot)

    def get_min_boundary_time(self, on_forward_graph):
        if on_forward_graph:
            return np.min(self.forward_boundary_time)
        else:
            return np.min(self.backward_boundary_time)

    def get_boundary_time_sum(self, on_forward_graph):
        if on_forward_graph:
            finite_numbers = self.forward_boundary_time[
                np.isfinite(self.forward_boundary_time)]
            return np.sum(finite_numbers)
        else:
            finite_numbers = self.backward_boundary_time[
                np.isfinite(self.backward_boundary_time)]
            return np.sum(finite_numbers)

    def get_priority_key(self, use_domination_value, on_forward_graph):
        if(use_domination_value):
            return -self.get_domination_value(on_forward_graph)
        else:
            return self.get_min_boundary_time(on_forward_graph)


# For converting the regions in the ArcFlags csv file back into binary from hex
def hex_deconverter(hex_string):
    new_str = bin(int(hex_string, 16))[2:]
    new_list = map(int, list(new_str))
    if len(new_list) < 400:
        new_list = [0] * (400 - len(new_list)) + new_list
    return new_list

##############################
#        NON ARC FLAG        #
##############################


# # Instead of using ID's as the keys, they use actual nodes.
# # Also sets up boundary nodes and arcflags.
# def fix_nodes(dict_of_nodes, has_speeds, has_arc_flags):
#     for node_id in dict_of_nodes:
#         curr_node = dict_of_nodes[node_id]
# 
#         # TODO: remove new_forward_links and forward_arc_flags
#         new_forward_links = []
#         forward_arc_flags = {}
#         backward_arc_flags = {}
# 
#         for connecting_link in curr_node.forward_links:
#             try:
#                 new_node = dict_of_nodes[connecting_link.origin_node_id]
#                 if new_node != -1:
#                     connecting_link.origin_node = curr_node
#                     connecting_link.connecting_node = new_node
#                     new_forward_links.append(connecting_link)
# 
#                     # Set is_forward_arc_flags[new_node] = secondDict{}
#                     # secondDict[RegionNumber] = True or False
#                     if has_arc_flags is None:
#                         curr_node.is_forward_arc_flags[new_node] = False
#                         curr_node.is_backward_arc_flags[new_node] = False
#                     else:
#                         # DEPRECATED
#                         forward_arc_flags[new_node] = (
#                             curr_node.is_forward_arc_flags[connecting_link])
#                         backward_arc_flags[new_node] = (
#                             curr_node.is_backward_arc_flags[connecting_link])
#             except(KeyError):
#                 pass
#         curr_node.forward_links = new_forward_links
#         if has_arc_flags is not None:
#             curr_node.is_forward_arc_flags = forward_arc_flags
#             curr_node.is_backward_arc_flags = backward_arc_flags
# 
#     for node_id in dict_of_nodes:
#         node = dict_of_nodes[node_id]
#         for connecting_link in node.forward_links:
#             connecting_node = connecting_link.connecting_node
#             if connecting_node is None:
#                 pass
#             connecting_node.backward_links.append(connecting_link)
#             if connecting_node.region != node.region:
#                 connecting_node.is_boundary_node = True


# Returns a set of nodes with all their forward_links properly set
def set_up_nodes(nyc_map, time_file, arc_flag_file):
    dict_of_links = nyc_map.links_by_node_id
    if time_file is not None:
        speed_of_links = csv.reader(open(time_file, 'rb'), delimiter=',')
    header = True
    # Adds speeds of links
    if speed_of_links is not None:
        for link in speed_of_links:
            if header:
                header = False
                continue
            orig_link = dict_of_links[(int(link[0]), int(link[1]))]
            orig_link.speed = float(link[3])  # Speed of link
            orig_link.time = float(link[4])  # Time of link

    header = True
    # Key is start_node, adds arc_links
    # TODO: figure out what to fill here for an arc_flag.csv
    """
    arc_flags = None
    if arc_flag_file is not None:
        arc_flags = csv.reader(open(arc_flag_file, 'rb'), delimiter=',')
    if arc_flags is not None:
        for link in arc_flags:
            if header:
                header = False
                continue
            pass
    """
    return set(nyc_map.nodes)


# Returns an array that goes like this
# [MaxLat, MinLat, MaxLong, MinLong]
def get_node_info(arr):
    node_info = [-1000, 1000, -1000, 1000]
    for node in arr:
        if float(node.lat) > node_info[0]:
            node_info[0] = float(node.lat)
        if float(node.lat) < node_info[1]:
            node_info[1] = float(node.lat)
        if float(node.long) > node_info[2]:
            node_info[2] = float(node.long)
        if float(node.long) < node_info[3]:
            node_info[3] = float(node.long)
    return node_info


# If no ArcFlags, arc_flag_file is None
def get_correct_nodes(nyc_map, time_file, arc_flag_file):
    nodes = set_up_nodes(nyc_map, time_file, arc_flag_file)
    if time_file is None:
        for node in nodes:
            for link in node.forward_links:
                link.speed = 5
                link.time = link.weight / 5
            for link in node.backward_links:
                link.speed = 5
                link.time = link.weight / 5
#     node_info = get_node_info(nodes)
#     return set_up_grid(
#         node_info[0] + .01, node_info[1], node_info[2] + .01, node_info[3],
#         num_divisions, nodes)


# Returns an array that goes like this
# [MaxLat, MinLat, MaxLong, MinLong]
def get_node_range(nyc_map):
    node_info = [-1000, 1000, -1000, 1000]
    for node in nyc_map.nodes:
        if float(node.lat) > node_info[0]:
            node_info[0] = float(node.lat)
        if float(node.lat) < node_info[1]:
            node_info[1] = float(node.lat)
        if float(node.long) > node_info[2]:
            node_info[2] = float(node.long)
        if float(node.long) < node_info[3]:
            node_info[3] = float(node.long)
    node_info[0] += .01
    node_info[2] += .01
    return node_info
