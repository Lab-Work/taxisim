import Queue


# Assigns each Boundary node an index in the list
def initialize_dictionary(list_of_boundary_nodes):
    i = 0
    dict_of_indices = dict()
    for node in list_of_boundary_nodes:
        dict_of_indices[node] = i
        i += 1
    return dict_of_indices


# Sets up lists of "INF" for each nodes, excluding boundary nodes
def initialize_nodes(dict_of_indices, list_of_boundary_nodes, grid_of_nodes):
    for column in grid_of_nodes:
        for region in column:
            for node in region.nodes:
                # Each node needs a distance from each boundary node
                # all starting at infinity
                node.time_from_boundary_node = [float("INF")] * (
                    len(list_of_boundary_nodes))
                node.arc_flag_paths = [None] * len(list_of_boundary_nodes)
                try:
                    # If it's in the dictionary, it's a boundary node
                    # and thus must be 0 away from itself
                    index = dict_of_indices[node]
                    node.time_from_boundary_node[index] = 0
                    node.was_updated.add(index)
                except(KeyError):
                    pass


# Every node in array nodes gets reset so it has no distance from anything
# no time from anything, and came from nothing (used to reset after making
# the path)
def reset_nodes(arr_nodes):
    for node in arr_nodes:
        if node is not None:
            node.came_from = None
            node.best_time = float("INF")
            node.arc_flag_paths = []
            node.time_from_boundary_nodes = []


# Basically creates a tree rooted at the boundary node where every edge in the
# tree is an arcflag
def singular_dijkstra(dist_dict, boundary_node, grid_of_nodes):
    # Keeps track of all the nodes we have completeed
    searchednodes = set()

    # Nodes we intend to search (somehow connected to graph so far).
    # We treat this as a priority queue: the one that has the potential to be
    # closest (has best distance from the start_node/is closest to the
    # end_node) is treated next
    nodes_to_search = Queue.PriorityQueue()
    nodes_in_queue = set()

    nodes_to_search.put((0, boundary_node))
    nodes_in_queue.add(boundary_node)

    boundary_node.best_time = 0
    while not nodes_to_search.empty():
        # Gets the node closest to the end node in the best case
        curr_node = nodes_to_search.get()[1]
        for connected_node in curr_node.backwards_connections:
            if connected_node.time_connections[curr_node] <= 0:
                continue
            if connected_node in searchednodes:
                continue

            # Checks distance thus far and the best case distance between this
            # point and the end point
            tentative_best = (
                float(connected_node.time_connections[curr_node]) +
                curr_node.best_time)

            # If we haven't queued it up to search yet, queue it up now.
            # Otherwise, for both of the next two if statements, place the best
            # path we've found thus far into that node
            if tentative_best < connected_node.best_time:
                connected_node.came_from = curr_node
                connected_node.best_time = tentative_best
                if connected_node not in nodes_in_queue:
                    nodes_to_search.put(
                        (connected_node.best_time, connected_node))
                    connected_node.in_queue = True
    compare_arc_flags(dist_dict, boundary_node, grid_of_nodes)
    for column in grid_of_nodes:
        for region in column:
            reset_nodes(region.nodes)


def compare_arc_flags(dist_dict, boundary_node, grid_of_nodes):
    for column in grid_of_nodes:
        for region in column:
            for node in region.nodes:
                if node.best_time != dist_dict[(boundary_node.id, node.id)]:
                    print "ERROR!: Single(" + str(node.best_time) + (
                        "), Multiple(" +
                        str(dist_dict[(boundary_node.id, node.id)]) + ")")
