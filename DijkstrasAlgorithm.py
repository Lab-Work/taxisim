import Queue


# An implementation of multi-origin dijkstra
class DijkstrasAlgorithm:
    # Assigns each Boundary node an index in the list
    @staticmethod
    def init_dict(list_of_boundary_nodes):
        i = 0
        boundary_indices = dict()
        for node in list_of_boundary_nodes:
            boundary_indices[node] = i
            i += 1
        return boundary_indices

    # Sets up lists of "INF" for each nodes, excluding boundary nodes
    @staticmethod
    def initialize_nodes(boundary_indices, boundary_nodes_list, grid_of_nodes):
        for column in grid_of_nodes:
            for region in column:
                for node in region.nodes:
                    # Each node needs a distance from each boundary node
                    # all starting at infinity
                    node.time_from_boundary_node = (
                        [float("INF")] * len(boundary_nodes_list))
                    # Store a deep copy snapshot of time_from_boundary_node for
                    # future comparison
                    node.time_snapshot = node.time_from_boundary_node[:]
                    node.arc_flag_paths = [None] * len(boundary_nodes_list)
                    if node in boundary_indices:
                        # If it's in the dictionary, it's a boundary node,
                        # and thus must be 0 away from itself
                        index = boundary_indices[node]
                        node.time_from_boundary_node[index] = 0
                        node.was_updated.add(index)

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
                node.was_updated = set()

    # Basically creates a tree rooted at the boundary node where every edge in
    # the tree is an arcflag
    @staticmethod
    def dijkstra(boundary_nodes, grid_of_nodes):
        max_queue_size = 0  # debug
        expansion_count = 0  # debug
        # Assign each boundary node an i for distance
        boundary_indices = DijkstrasAlgorithm.init_dict(boundary_nodes)

        # Gives each node a distance from the boundary nodes, which are
        # initially either INF(infinity) or 0
        DijkstrasAlgorithm.initialize_nodes(boundary_indices, boundary_nodes,
                                            grid_of_nodes)

        # Nodes we intend to search (somehow connected to graph so far). We
        # treat this as a priority queue: the one that has the potential to be
        # closest (has best distance from the start_node/is closest to the
        # end_node) is treated next
        nodes_to_search = Queue.PriorityQueue()

        # Checks to see if the node is already in the queue (True means it is
        # in it False means it is not)
        for node in boundary_nodes:
            nodes_to_search.put((
                # times updated since it was last expanded
                0,
                # minimum time from boundary node
                0,
                # number of infinities in the list
                len(node.time_from_boundary_node) - 1,
                # sum of non infinities in the list
                0,
                # the actual node itself
                node))
        counter = 0
        while not nodes_to_search.empty():
            # Gets the node closest to the end node in the best case
            counter += 1
            if (nodes_to_search.qsize() > max_queue_size):
                max_queue_size = nodes_to_search.qsize()
            if counter % 10000 == 0:
                print nodes_to_search.qsize()
            queue_item = nodes_to_search.get()
            old_min_time, old_inf_count, old_sum = queue_item[1:4]
            curr_node = queue_item[4]
            # Skip if the item in queue is out-dated
            if (old_min_time > curr_node.get_min_boundary_time() or
                    old_inf_count > curr_node.get_boundary_time_inf_count() or
                    old_sum < node.get_boundary_time_sum()):
                continue

            # expansion of curr_node starts here
            expansion_count += 1
            for connected_node in curr_node.backwards_connections:
                has_updates = False
                # Overwrite the snapshot with a copy of the current label
                curr_node.time_snapshot = (
                    curr_node.time_from_boundary_node[:])
                for i in curr_node.was_updated:
                    if connected_node.time_connections[curr_node] <= 0:
                        continue
                    # Checks distance thus far and the best case distance
                    # between this point and the end point
                    tmp_best = (
                        float(connected_node.time_connections[curr_node]) +
                        curr_node.time_from_boundary_node[i])

                    # If we haven't queued it up to search yet, queue it up now
                    # Otherwise, for both of the next two if statements, place
                    # the best path we've found thus far into that node
                    if tmp_best < connected_node.time_from_boundary_node[i]:
                        has_updates = True
                        connected_node.was_updated.add(i)
                        connected_node.arc_flag_paths[i] = curr_node
                        connected_node.time_from_boundary_node[i] = tmp_best
                        # Sorts them by their smallest value if they are
                        # not in the queue
                if has_updates and connected_node.get_domination_value() > 0:
                    nodes_to_search.put((
                        # times updated since it was last expanded
                        connected_node.get_domination_value(),
                        # minimum time from boundary node
                        connected_node.get_min_boundary_time(),
                        # number of infinities in the list
                        connected_node.get_boundary_time_inf_count(),
                        # sum of non infinities in the list
                        connected_node.get_boundary_time_sum(),
                        # the actual node itself
                        connected_node))
            curr_node.was_updated = set()  # end while

        DijkstrasAlgorithm.set_arc_flags(grid_of_nodes)

        print "Max Queue Size:", max_queue_size  # debug
        print "Number of expansions:", expansion_count  # debug

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
