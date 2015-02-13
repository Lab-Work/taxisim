from Node import *
#from Map import Map
from Queue import PriorityQueue
from random import randint
from datetime import datetime

HEURISTIC_DISCOUNT = .8


# Uses bidirectional search to find the shortest path between start_node and end_node
# Params:
# start_node - the node at the beginning of the path
# end_node - the node at the end of the path
# use_astar - use euclidean distance heuristic to guide the search using A*
# use_arcflags - if arcflags are pre-computed on the links, search can be drastically improved
# max_speed - maximum speed on any link in the graph. used for the A* heuristic
# Returns:
# path - a list of Links on the shortest path, in order, or None if no such path exists
def bidirectional_search(
        start_node,
        end_node,
        use_astar=False,
        use_arcflags=False,
        max_speed=1.0):
    # Step 1 - perform the actual dijkstra search
    (center_node,
     forward_pq,
     forward_expanded,
     backward_pq,
     backward_expanded) = bidirectional_dijkstra(start_node,
                                                 end_node,
                                                 use_astar,
                                                 use_arcflags,
                                                 max_speed)

    if(center_node==None):
        return None
    # Step 2 - reconstruct the path, using the pointers left on the node objects
    path = reconstruct_path(center_node)

    # Step 3 - clean up (reset pointers and time costs on node objects)
    # Note that we only need to do this on nodes touched by the search
    cleanup(forward_pq, forward_expanded, backward_pq, backward_expanded)
    return path

# Helper method - you should probably call bidirectiona_search() instead, since that also cleans up after
# Runs a forward and backward dijkstra algorithms, stopping when they meet.  Leaves pointers and partial
# distances on the node objects touched by the search. These can be used to quickly construct the path by reconstruct_path()
# For more information about bidirectional A* search heuristics and stop criteria, see:
# "A Fast Algorithm for Finding Better Routes by AI Search Techniques", Ikeda et al., 1994
# Params:
    # start_node - the node at the beginning of the path
    # end_node - the node at the end of the path
    # use_astar - use euclidean distance heuristic to guide the search using A*
    # use_arcflags - if arcflags are pre-computed on the links, search can be drastically improved
    # max_speed - maximum speed on any link in the graph, used for the A* heuristic
# Returns:
    # path - a list of Links on the shortest path, in order
    # num_expanded - the number of nodes that were expanded during hte search


def bidirectional_dijkstra(
        start_node,
        end_node,
        use_astar=False,
        use_arcflags=False,
        max_speed=1.0):
    # Initialize the priority queue for the forward search from the origin
    forward_pq = PriorityQueue()
    start_node.forward_time = 0
    forward_pq.put((0, None, start_node))
    forward_expanded = []

    # Initialize the priority queue for the backward search from the destination
    backward_pq = PriorityQueue()
    end_node.backward_time = 0
    backward_pq.put((0, None, end_node))
    backward_expanded = []

    best_full_time = float('inf')
    center_node = None

    # The main loop alternates between forward and backward expansions
    while(not forward_pq.empty() and not backward_pq.empty()):

        #### FORWARD EXPANSION ####
        (cost, link, node) = forward_pq.get()
        forward_expanded.append(node)
        node.was_forward_expanded = True

        # If this node has been touched by both searches, it is potentially the center node
        # The center node is the node which has the shortest total distance to
        # the origin and destination
        if(node.backward_time + node.forward_time < best_full_time):
            best_full_time = node.backward_time + node.forward_time
            center_node = node

        # If this node was already expanded by the backward search, then the two
        # searches have met each other - we are done
        if(node.was_backward_expanded):
            break

        # propagate to neighboring nodes
        for link in node.forward_links:
            # Proposed time of reaching this neighbor via this node
            proposed_cost = node.forward_time + link.time

            # If this is better than the current path, then make the update and
            # add that neighbor to the PQ
            if(proposed_cost < link.connecting_node.forward_time):
                link.connecting_node.forward_time = proposed_cost
                link.connecting_node.forward_predecessor_link = link

                # If we are using A*, then the priority is modified with a
                # heuristic function
                if(use_astar):
                    # for bidirectional search, we must consider both the forward cost and backward cost, in order to guarantee admissibility
                    # We take half of their difference as in
                    # "A Fast Algorithm for Finding Better Routes by AI Search Techniques", Ikeda et al., 1994
                    distance_difference = end_node.approx_dist_to(
                        link.connecting_node) - start_node.approx_dist_to(link.connecting_node)
                    proposed_cost += (distance_difference / 
                                      max_speed) * (HEURISTIC_DISCOUNT / 2)
                forward_pq.put((proposed_cost, link, link.connecting_node))

        #### BACKWARD EXPANSION ####
        (cost, link, node) = backward_pq.get()
        backward_expanded.append(node)
        node.was_backward_expanded = True

        # If this node has been touched by both searches, it is potentially the center node
        # The center node is the node which has the shortest total distance to
        # the origin and destination
        if(node.backward_time + node.forward_time < best_full_time):
            best_full_time = node.backward_time + node.forward_time
            center_node = node

        # If this node was already expanded by the forward search, then the two searches have met
        # We are done
        if(node.was_forward_expanded):
            break

        # propagate to neighboring nodes
        for link in node.backward_links:
            # Proposed time of reaching this neighbor via this node
            proposed_cost = node.backward_time + link.time

            # If this is better than the current path, then make the update and
            # add that neighbor to the PQ
            if(proposed_cost < link.origin_node.backward_time):
                link.origin_node.backward_time = proposed_cost
                link.origin_node.backward_predecessor_link = link

                # If we are using A*, then the priority is modified with a
                # heuristic function
                if(use_astar):
                    distance_difference = start_node.approx_dist_to(
                        link.origin_node) - end_node.approx_dist_to(link.origin_node)
                    proposed_cost += (distance_difference / 
                                      max_speed) * (HEURISTIC_DISCOUNT / 2)
                backward_pq.put((proposed_cost, link, link.origin_node))

    if(center_node is None):
        print("Bidirectional search has failed.")

    return (
        center_node,
        forward_pq,
        forward_expanded,
        backward_pq,
        backward_expanded)

# Uses the output from bidirectional_dijkstra() to reconstruct the shortest path
# Params:
    # center_node - the node where the forward and backward searches met - output by bidirectional_dijkstra()
# Returns:
    # path - a list of Links on the shortest path, in order


def reconstruct_path(center_node):
    # At this point, the forward search and backward search have met at center_node
    # The path consists of two parts
    # 1) The links leading from the center_node to the origin, which must be reversed
    # 2) The links leading from the center_node to the destination, which do
    # not need to be reversed

    # Reconstruct first part of the path
    first_part = []
    node = center_node
    while(node.forward_predecessor_link is not None):
        first_part.append(node.forward_predecessor_link)
        node = node.forward_predecessor_link.origin_node

    # Reconstruct second part of the path
    second_part = []
    node = center_node
    while(node.backward_predecessor_link is not None):
        second_part.append(node.backward_predecessor_link)
        node = node.backward_predecessor_link.connecting_node

    # Reverse the first part and combine
    return list(reversed(first_part)) + second_part

# Cleans up the mess made by bidirectional_dijkstra()
# It resets the pointers and time costs on node objects which were touched by the search
# The four inputs come directly from the outputs of bidirectional_dijkstra
# Collectively, they represent all of the nodes that were touched by the search


def cleanup(forward_pq, forward_expanded, backward_pq, backward_expanded):
    for node_pq in [forward_pq, backward_pq]:
        if(node_pq is not None):
            for (priority, node) in node_pq.queue:
                node.reset()

    for node_list in [forward_expanded, backward_expanded]:
        if(node_list is not None):
            for node in node_list:
                node.reset()


# A simple one-directional Dijkstra search from start_node to end_node
# Slower than the bidirectional search, this is mostly needed for testing purposes
# Params:
    # start_node - the node at the beginning of the path
    # end_node - the node at the end of the path
    # use_astar - use euclidean distance heuristic to guide the search using A*
    # use_arcflags - if arcflags are pre-computed on the links, search can be drastically improved
    # max_speed - maximum speed on any link in the graph. used for the A* heuristic
# Returns:
    # path - a list of Links on the shortest path, in order
def simple_dijkstra(
        start_node,
        end_node,
        use_astar=False,
        use_arcflags=False,
        max_speed=1.0):
    # Initialize the priority queue for the forward search from the origin
    forward_pq = PriorityQueue()
    start_node.forward_time = 0
    forward_pq.put((0, start_node))
    forward_expanded = []

    # The main loop alternates between forward and backward expansions
    while(not forward_pq.empty()):

        # FORWARD EXPANSION
        (cost, node) = forward_pq.get()
        forward_expanded.append(node)
        # If this node has already been expanded by the backward search, then we
        # have met in the middle - we are done
        if(node == end_node):
            break

        # propagate to neighboring nodes
        for link in node.forward_links:
            # Proposed time of reaching this neighbor via this node
            proposed_cost = node.forward_time + link.time

            # If this is better than the current path, then make the update and
            # add that neighbor to the PQ
            if(proposed_cost < link.connecting_node.forward_time):
                link.connecting_node.forward_time = proposed_cost
                link.connecting_node.forward_predecessor_link = link

                if(use_astar):
                    proposed_cost += (
                        end_node.approx_dist_to(
                            link.connecting_node) / max_speed) * HEURISTIC_DISCOUNT

                forward_pq.put((proposed_cost, link.connecting_node))

    # Reconstruct the path up to the end node, using the
    # forward_predecessor_links
    path = reconstruct_path(end_node)

    cleanup(forward_pq, forward_expanded, None, None)

    return path


###################### TESTING CODE ###################################

# choose a random node on the map
def choose_random_node(grid_of_nodes):
    l = []

    while(len(l) == 0):
        i = randint(0, len(grid_of_nodes) - 1)
        j = randint(0, len(grid_of_nodes[i]) - 1)

        l = list(grid_of_nodes[i][j].nodes)

    i = randint(0, len(l) - 1)
    return l[i]

# Find the maximum speed of any Link in hte graph


def get_max_speed(grid_of_nodes):
    max_speed = 0.0
    for row in grid_of_nodes:
        for col in row:
            for node in col.nodes:
                for link in node.forward_links:
                    max_speed = max(max_speed, link.speed)
                # for link in node.backward_links:
                #    max_speed = max(max_speed, link.speed)
    return max_speed


# Compares two paths, showing where they differ, and their total lengths
def compare_paths(p1, p2):
    p1_len = 0.0
    p2_len = 0.0

    for i in range(max(len(p1), len(p2))):
        if(i < len(p1)):
            p1_str = str(p1[i].origin_node.node_id) + \
                " --> " + str(p1[i].connecting_node.node_id)
            p1_len += p1[i].time
        else:
            p1_str = "                         "

        if(i < len(p2)):
            p2_str = str(p2[i].origin_node.node_id) + \
                " --> " + str(p2[i].connecting_node.node_id)
            p2_len += p2[i].time
        else:
            p2_str = "                         "

        decorator = " "

        if i >= len(p1) or i >= len(p2) or p1[i] != p2[i]:
            decorator += " !!!! "

        print p1_str + "   |   " + p2_str + decorator
    print str(p1_len) + "         |          " + str(p2_len)


# Randomly generate a bunch of origin,destination pairs from the graph
def generateSamples(grid_of_nodes, num_samples):
    samples = []
    for x in range(num_samples):
        orig = choose_random_node(grid_of_nodes)
        dest = choose_random_node(grid_of_nodes)
        samples.append((orig, dest))
    return samples

# Builds a dictionary that can look up node objects by id number


def build_nodes_by_id(grid_of_nodes):
    nodes_by_id = {}
    for row in grid_of_nodes:
        for col in row:
            for node in col.nodes:
                nodes_by_id[node.node_id] = node
    return nodes_by_id


# runs a bunch of queries between random points with several different
# methods, and compares the resulst
def bigComparison(num_trials):
    # Load the map
    print("Loading...")
    grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)
    max_speed = get_max_speed(grid_of_nodes)
    print("Max speed = " + str(max_speed))
    print("Choosing")

    samples = generateSamples(grid_of_nodes, num_trials)

    correct_paths = []
    t1 = datetime.now()
    for (orig, dest) in samples:
        path = simple_dijkstra(orig, dest)
        correct_paths.append(path)
    t2 = datetime.now()
    print "Single direction: " + str(t2 - t1)

    t1 = datetime.now()
    num_mistakes = 0
    for i in range(len(samples)):
        (orig, dest) = samples[i]
        path = simple_dijkstra(orig, dest, use_astar=True, max_speed=max_speed)
        if(path != correct_paths[i]):
            num_mistakes += 1
            print (orig.node_id, dest.node_id)
            compare_paths(correct_paths[i], path)
        correct_paths.append(path)
    t2 = datetime.now()
    print "Single dir A*   : " + str(t2 - t1)
    print "num mistakes = " + str(num_mistakes)

    t1 = datetime.now()
    num_mistakes = 0
    for i in range(len(samples)):
        (orig, dest) = samples[i]
        path = bidirectional_search(orig, dest)
        if(path != correct_paths[i]):
            num_mistakes += 1
            print (orig.node_id, dest.node_id)
            compare_paths(correct_paths[i], path)
        correct_paths.append(path)
    t2 = datetime.now()
    print "Bidirectional  : " + str(t2 - t1)
    print "num mistakes = " + str(num_mistakes)

    t1 = datetime.now()
    num_mistakes = 0
    for i in range(len(samples)):
        (orig, dest) = samples[i]
        path = bidirectional_search(
            orig,
            dest,
            use_astar=True,
            max_speed=max_speed)
        if(path != correct_paths[i]):
            num_mistakes += 1
            print (orig.node_id, dest.node_id)
            compare_paths(correct_paths[i], path)
        correct_paths.append(path)
    t2 = datetime.now()
    print "Bidirectional A*: " + str(t2 - t1)
    print "num mistakes = " + str(num_mistakes)


# Tests a few problematic origin,destination pairs for debugging
def test_specific_paths():
    print("Loading...")
    grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)
    max_speed = get_max_speed(grid_of_nodes)
    print("Max speed = " + str(max_speed))

    nodes_by_id = build_nodes_by_id(grid_of_nodes)

    od_pairs = [('42446466', '42976341'),
                ('103100314', '766749616'),
                ('42729538', '42828433'),
                ('261345962', '103878615'),
                ('42986423', '293348934'),
                ('2548100071', '42517576'),
                ('42427863', '103220021'),
                ('103754204', '254693611'),
                ('42764952', '42467168')]

    for(origin_id, dest_id) in od_pairs:
        print(origin_id, dest_id)
        orig, dest = nodes_by_id[origin_id], nodes_by_id[dest_id]
        path1 = simple_dijkstra(orig, dest)
        print("Dijkstra expanded: " + str(expanded1))
        path2 = bidirectional_search(orig, dest)
        print("Bidirectional expanded: " + str(expanded2))
        path3 = simple_dijkstra(orig, dest, use_astar=True, max_speed=max_speed)
        print("A* expanded: " + str(expanded3))
        path4 = bidirectional_search(
            orig,
            dest,
            use_astar=True,
            max_speed=max_speed)
        print("Bidirectional A* expanded: " + str(expanded4))
        print path2 == path1
        compare_paths(path1, path2)
        print path3 == path1
        compare_paths(path1, path3)
        print path4 == path1
        compare_paths(path1, path4)
        print
        print

# Given a list of (origin,destination) pairs, runs all of the shortest path queries
# use_bidirectional and use_astar control which algorithm will be used


def run_many_queries(od_list, use_bidirectional, use_astar, max_speed):
    paths = []
    t1 = datetime.now()
    for (orig, dest) in od_list:
        if(use_bidirectional):
            path = bidirectional_search(
                orig,
                dest,
                use_astar=use_astar,
                max_speed=max_speed)
        else:
            path = simple_dijkstra(
                orig,
                dest,
                use_astar=use_astar,
                max_speed=max_speed)
        paths.append(path)
    t2 = datetime.now()
    return paths, t2 - t1


# Tests the search algorithms on real origin,destination pairs from the
# taxi data, and compares performance
def test_with_real_data():
    print("Loading...")

    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    max_speed = nyc_map.get_max_speed()

    print("Max speed = " + str(max_speed))

    print("Reading file")
    sample_trips = []
    with open('sample.csv', 'r') as f:
        r = csv.reader(f)
        r.next()  # throw out header
        for line in r:
            [medallion,
             hack_license,
             vendor_id,
             rate_code,
             store_and_fwd_flag,
             pickup_datetime,
             dropoff_datetime,
             passenger_count,
             trip_time_in_secs,
             trip_distance,
             pickup_longitude,
             pickup_latitude,
             dropoff_longitude,
             dropoff_latitude] = line

            [pickup_longitude,
             pickup_latitude,
             dropoff_longitude,
             dropoff_latitude] = map(float,
                                     [pickup_longitude,
                                      pickup_latitude,
                                      dropoff_longitude,
                                      dropoff_latitude])
            sample_trips.append(
                [pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude])
            if(len(sample_trips) >= 1000):
                break

    print("Matching nodes.")
    t1 = datetime.now()
    od_list = []
    for [
            pickup_longitude,
            pickup_latitude,
            dropoff_longitude,
            dropoff_latitude] in sample_trips:

        orig = nyc_map.get_nearest_node(pickup_latitude, pickup_longitude)
        # print "calls : " + str(nyc_map.lookup_kd_tree.calls)
        dest = nyc_map.get_nearest_node(dropoff_latitude, dropoff_longitude)
        # print "calls : " + str(nyc_map.lookup_kd_tree.calls)
        # orig = find_nodes(pickup_longitude, pickup_latitude, grid_of_nodes, node_info, 20)
        # dest = find_nodes(dropoff_longitude, dropoff_latitude, grid_of_nodes, node_info, 20)
        if(orig is not None and dest is not None):
            od_list.append((orig, dest))
    t2 = datetime.now()
    print "Finding " + str(len(od_list)) + " nodes : " + str(t2 - t1)

    for use_bi in [False, True]:
        for use_astar in [False, True]:
            paths, time = run_many_queries(
                od_list, use_bi, use_astar, max_speed)

            if(use_bi):
                out = "BiDirectional "
            else:
                out = ""

            if(use_astar):
                out += "A* "
            else:
                out += "Dijkstra "

            out += str(time)
            print out

            if(not use_bi and not use_astar):
                ground_truth = paths
            else:
                mistakes = 0
                for i in range(len(paths)):
                    if(paths[i] != ground_truth[i]):
                        mistakes += 1
                print "Mistakes : " + str(mistakes)


if(__name__ == "__main__"):
    # bigComparison(100)
    # test_specific_paths()
    test_with_real_data()
