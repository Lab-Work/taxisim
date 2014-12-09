from Node import *
from Queue import PriorityQueue
from random import randint
from datetime import datetime
from MITSpeedAlgorithm import find_nodes

from matplotlib import pyplot as plt

HEURISTIC_DISCOUNT = .8


# Uses bidirectional search to find the shortest path between start_node
# and end_node
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

    # Step 2 - reconstruct the path, using the pointers left on the node
    # objects
    path = reconstruct_path(center_node)

    num_expanded = len(forward_expanded) + len(backward_expanded)

    # Step 3 - clean up (reset pointers and time costs on node objects)
    # Note that we only need to do this on nodes touched by the search
    cleanup(forward_pq, forward_expanded, backward_pq, backward_expanded)
    return path, num_expanded


# Runs a forward and backward dijkstra algorithms, stopping when they meet.  Leaves pointers and partial
# distances on the node objects touched by the search. These can be used to quickly construct the path by reconstruct_path()
# Params:
    # start_node - the node at the beginning of the path
    # end_node - the node at the end of the path
    # use_astar - use euclidean distance heuristic to guide the search using A*
    # use_arcflags - if arcflags are pre-computed on the links, search can be drastically improved
    # max_speed - used for the A* heuristic
def bidirectional_dijkstra(
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

    # Initialize the priority queue for the backward search from the
    # destination
    backward_pq = PriorityQueue()
    end_node.backward_time = 0
    backward_pq.put((0, end_node))
    backward_expanded = []

    best_full_time = float('inf')
    center_node = None

    i = 0
    # The main loop alternates between forward and backward expansions
    while(not forward_pq.empty() and not backward_pq.empty()):

        #### FORWARD EXPANSION ####
        (cost, node) = forward_pq.get()
        forward_expanded.append(node)
        node.was_forward_expanded = True

        # If this node has been touched by both searches, it is potentially the center node
        # The center node is the node which has the shortest total distance to
        # the origin and destination
        if(node.backward_time + node.forward_time < best_full_time):
            best_full_time = node.backward_time + node.forward_time
            center_node = node

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

        #### BACKWARD EXPANSION ####
        (cost, node) = backward_pq.get()
        backward_expanded.append(node)
        node.was_backward_expanded = True

        # If this node has been touched by both searches, it is potentially the center node
        # The center node is the node which has the shortest total distance to
        # the origin and destination
        if(node.backward_time + node.forward_time < best_full_time):
            best_full_time = node.backward_time + node.forward_time
            center_node = node

        # propagate to neighboring nodes
        for link in node.backward_links:
            # Proposed time of reaching this neighbor via this node
            proposed_cost = node.backward_time + link.time

            # If this is better than the current path, then make the update and
            # add that neighbor to the PQ
            if(proposed_cost < link.origin_node.backward_time):
                link.origin_node.backward_time = proposed_cost
                link.origin_node.backward_predecessor_link = link

                if(use_astar):
                    proposed_cost += (
                        start_node.approx_dist_to(
                            link.origin_node) / max_speed) * HEURISTIC_DISCOUNT
                backward_pq.put((proposed_cost, link.origin_node))

        ##### TERMINATION CONDITION #####
        (forward_cost, forward_node) = forward_pq.queue[0]
        (backward_cost, backward_node) = backward_pq.queue[0]
        if(use_astar and center_node is not None):
            # penalty = (center_node.forward_time + center_node.backward_time) - (start_node.approx_dist_to(end_node) / max_speed) * .9
            penalty = (
                center_node.forward_time + center_node.backward_time) - (
                start_node.approx_dist_to(center_node) / max_speed) * HEURISTIC_DISCOUNT - (
                end_node.approx_dist_to(center_node) / max_speed) * HEURISTIC_DISCOUNT

        else:
            penalty = 0

        if(forward_node.forward_time + backward_node.backward_time > best_full_time + penalty):
            break

        if(i % 2000 == 0):
            print"*******************"
            plt.cla()
            x_coords1 = [n.long for n in forward_expanded]
            y_coords1 = [n.lat for n in forward_expanded]
            x_coords2 = [n.long for n in backward_expanded]
            y_coords2 = [n.lat for n in backward_expanded]

            print len(x_coords1)

            plt.scatter(x_coords1, y_coords1, color="green")
            plt.scatter(x_coords2, y_coords2, color="red")
            plt.scatter([start_node.long], [start_node.lat], color="black")
            plt.scatter([end_node.long], [end_node.lat], color="black")

            plt.show()

        i += 1

    """
    #Now, we need to find the center node of the search - the node that has the shortest
    #forward_time + backward_time.  Note that this may  not necessarily be the node
    #that caused the search to end.  It may be some other node which was touched by both
    #searches
    center_node=None
    for node in possible_center_nodes:
        if(center_node == None or node.forward_time + node.backward_time < center_node.forward_time + center_node.backward_time):
            center_node = node
    """

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
    # center_node - the node where the forward and backward searches met -
    # output by bidirectional_dijkstra()


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
        # If this node has already been expanded by the backward search, then
        # we have met in the middle - we are done
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

    path = reconstruct_path(end_node)

    cleanup(forward_pq, forward_expanded, None, None)

    return path, len(forward_expanded)


###################### TESTING CODE ###################################


def choose_random_node(grid_of_nodes):
    l = []

    while(len(l) == 0):
        i = randint(0, len(grid_of_nodes) - 1)
        j = randint(0, len(grid_of_nodes[i]) - 1)

        l = list(grid_of_nodes[i][j].nodes)

    i = randint(0, len(l) - 1)
    return l[i]


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


def slow_reset(grid_of_nodes):
    for row in grid_of_nodes:
        for col in row:
            for node in col.nodes:
                node.reset()


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

        # print p1_str + "   |   " + p2_str + decorator
    print str(p1_len) + "         |          " + str(p2_len)


def generateSamples(grid_of_nodes, num_samples):
    samples = []
    for x in range(num_samples):
        orig = choose_random_node(grid_of_nodes)
        dest = choose_random_node(grid_of_nodes)
        samples.append((orig, dest))
    return samples


def build_nodes_by_id(grid_of_nodes):
    nodes_by_id = {}
    for row in grid_of_nodes:
        for col in row:
            for node in col.nodes:
                nodes_by_id[node.node_id] = node
    return nodes_by_id


def bigComparison():
    # Load the map
    print("Loading...")
    grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)
    max_speed = get_max_speed(grid_of_nodes)
    print("Max speed = " + str(max_speed))
    print("Choosing")

    samples = generateSamples(grid_of_nodes, 1000)

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
        path, expanded2 = bidirectional_search(orig, dest)
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
        path, expanded2 = bidirectional_search(
            orig, dest, use_astar=True, max_speed=max_speed)
        if(path != correct_paths[i]):
            num_mistakes += 1
            print (orig.node_id, dest.node_id)
            compare_paths(correct_paths[i], path)
        correct_paths.append(path)
    t2 = datetime.now()
    print "Bidirectional A*: " + str(t2 - t1)
    print "num mistakes = " + str(num_mistakes)


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
        path1, expanded1 = simple_dijkstra(orig, dest)
        print("Dijkstra expanded: " + str(expanded1))
        path2, expanded2 = bidirectional_search(orig, dest)
        print("Bidirectional expanded: " + str(expanded2))
        path3, expanded3 = simple_dijkstra(
            orig, dest, use_astar=True, max_speed=max_speed)
        print("A* expanded: " + str(expanded3))
        path4, expanded4 = bidirectional_search(
            orig, dest, use_astar=True, max_speed=max_speed)
        print("Bidirectional A* expanded: " + str(expanded4))
        print path2 == path1
        compare_paths(path1, path2)
        print path3 == path1
        compare_paths(path1, path3)
        print path4 == path1
        compare_paths(path1, path4)
        print
        print


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


def test_with_real_data():
    print("Loading...")
    grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)
    max_speed = get_max_speed(grid_of_nodes)
    node_info = get_node_range(grid_of_nodes)
    print("Max speed = " + str(max_speed))

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
            if(len(sample_trips) >= 10000):
                break

    t1 = datetime.now()
    od_list = []
    for [
            pickup_longitude,
            pickup_latitude,
            dropoff_longitude,
            dropoff_latitude] in sample_trips:
        orig = find_nodes(
            pickup_longitude,
            pickup_latitude,
            grid_of_nodes,
            node_info,
            20)
        dest = find_nodes(
            dropoff_longitude,
            dropoff_latitude,
            grid_of_nodes,
            node_info,
            20)
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


if(__name__ == "__main__"):
    # bigComparison()
    test_specific_paths()
    # test_with_real_data()
