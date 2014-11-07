import Queue
from GraphLib import distance

# USES A COMBINATION OF A* AND ARCFLAGS TO ROUTE FROM ONE PLACE TO ANOTHER
# (ALSO FINDS START AND END NODES)


def heuristic(node, end_node, max_speed):
    return distance(node.lat, node.long, end_node.lat, end_node.long)/max_speed


# Finds if a Trip's data is out of bounds of our node data
# (nodes have region centered at (x,y)  with radius r_1, trips are sporadic)
def out_of_bounds(longitude, latitude, node_info):
    if latitude >= node_info[0] or latitude < node_info[1] or (
            longitude >= node_info[2] or longitude < node_info[3]):
        return True
    return False


# Given a longitude and latitude, figures out which node is closest to it
def find_nodes(longitude, latitude, grid_of_nodes, node_info, n):
    if out_of_bounds(longitude, latitude, node_info):
        print "OUT OF BOUNDS: (Long, Lat) = (" + (
            str(longitude) + ", " + str(latitude) + ")")
        return None
    # node closest to coords and its distance
    best_node = None
    best_dist = 1000000
    i = int(float(longitude - node_info[3]) * (
        n / float(node_info[2] - node_info[3])))
    j = int(float(latitude - node_info[1]) * (
        n / float(node_info[0] - node_info[1])))

    # You have to check the surrounding area (if a coordinate is really close
    # to the edge of the region[i][j] it could be in a different region
    # [i - 1][j] for example
    if i != 0:
        i -= 1
    if j != 0:
        j -= 1
    for n in range(3):
        if i + n >= len(grid_of_nodes):
            break
        for m in range(3):
            if j + m >= len(grid_of_nodes[0]):
                break
            grid_region = grid_of_nodes[i + n][j + m]
            for node in grid_region.nodes:
                curr_dist = distance(latitude, longitude, node.lat, node.long)
                if curr_dist < best_dist and (
                        len(node.forward_links) > 0):
                    best_node = node
                    best_dist = curr_dist
    return best_node


# Every node in array nodes gets reset so it has no distance from anything,
# no time from anything, and came from nothing
# (used to reset after making the path)
def reset_nodes(arr_nodes):
    for node in arr_nodes:
        if node is not None:
            node.came_from = None
            node.best_time = float("INF")


def arcFlags(start_long, start_lat, end_long, end_lat, grid_of_nodes,
             node_info, n, max_speed):
    node1 = find_nodes(start_long, start_lat, grid_of_nodes, node_info, n)
    node2 = find_nodes(end_long, end_lat, grid_of_nodes, node_info, n)
    if node1 is None or node2 is None:
        print "COULDN'T FIND NODE"
        return 10000000
    return find_shortest_path(node1, node2, max_speed)


# Returns the shortest path between two nodes
# (Can modify to return the length instead, anything really)
# Using the A* algorithm
# http://en.wikipedia.org/wiki/A*_search_algorithm
def find_shortest_path(start_node, end_node, max_speed):

    # nodes that we've already traversed and thus will not search again
    searched_nodes = set()

    # nodes we intend to search (somehow connected to graph so far).
    # We treat this as a priority queue: the one that has the potential to be
    # closest (has best distance from the start_node/is closest to the
    # end_node) is treated next
    nodes_to_search = Queue.PriorityQueue()
    nodes_to_search.put((0, start_node))
    nodes_to_search2 = set()
    nodes_to_search2.add(start_node)
    start_node.best_time = 0
    while not nodes_to_search.empty():
        # Gets the node closest to the end node in the best case
        curr_node = nodes_to_search.get()[1]
        searched_nodes.add(curr_node)
#        nodes_to_search2.remove(curr_node)

        # End of the path - we found it! Now we just need to reset all the
        # nodes so they are at their default (no distance, no came_from)
        if curr_node == end_node:
            # This returns a list of nodes, in order of traversal (
            # final_path[0] = start_node,
            # final_path[len(final_path) - 1] = end_node)
            final_path = rebuild_path(curr_node)
            reset_nodes(nodes_to_search2)
            reset_nodes(searched_nodes)
            return final_path
        for connected_node in curr_node.forward_links:
            # THE ARCFLAGS PORTION
            if curr_node.is_forward_arc_flags[connected_node][end_node.region] == 0:
                if curr_node.region != end_node.region:
                    continue

            # If we've searched it before or it is non-existent, continue
            if curr_node.forward_links[connected_node].time <= 0:
                continue
            if connected_node in searched_nodes:
                continue

            # Checks distance thus far and the best case distance between this
            # point and the endpoint
            tentative_best = (float(
                curr_node.forward_links[connected_node].time) +
                curr_node.best_time)

            # If we haven't queued it up to search yet, queue it up now.
            # Otherwise, for both of the next two if statements, place the best
            # path we've found thus far into that node
            if tentative_best < connected_node.best_time:
                connected_node.came_from = curr_node
                connected_node.best_time = tentative_best
                nodes_to_search.put(
                    (heuristic(connected_node, end_node, max_speed) +
                        connected_node.best_time, connected_node))
                nodes_to_search2.add(connected_node)
    print start_node.node_id
    print end_node.node_id
    reset_nodes(nodes_to_search2)
    reset_nodes(searched_nodes)
    return "No Path Found"


# Given where the nodes came from
# rebuilds the path that was taken to the final node
def rebuild_path(node):
    arr = []
    while node is not None:
        arr.append(node)
        node = node.came_from
    return arr[::-1]
