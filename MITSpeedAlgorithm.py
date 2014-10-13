import csv
import timeit
from datetime import datetime
from Node import get_correct_nodes, get_node_range
import AStar.aStar
from math import sqrt
import Trip

##########################################
#                                        #
#               FUNCTIONS                #
#                                        #
##########################################


# Standard Euclidean distance multiplied given our region of space (NYC),
# where I converted it to a plane using Spherical -> cartesian coordinates.
def distance(lat1, long1, lat2, long2):
    diff_lat = float(lat1) - float(lat2)
    diff_long = float(long1) - float(long2)
    # meters per degree latitude
    # an approximation  based off our latitude and longitude
    lat_miles = diff_lat * 111194.86461
    # meters per degree longitude
    # an approximation  based off our latitude and longitude
    long_miles = diff_long * 84253.1418965
    return sqrt(lat_miles * lat_miles + long_miles * long_miles)


def out_of_bounds(longitude, latitude, node_info):
    if latitude >= node_info[0] or (
            latitude < node_info[1] or
            longitude >= node_info[2] or
            longitude < node_info[3]):
        return True
    return False


# Given a longitude and latitude, figures out which node is closest to it
def find_nodes(longitude, latitude, grid_of_nodes, node_info, n):
    if out_of_bounds(longitude, latitude, node_info):
        # print "OUT OF BOUNDS:
        # (Long, Lat) = (" + str(longitude) + ", " + str(latitude) + ")"
        return None
    # node closest to coords and its distance
    best_node = None
    best_distance = 1000000
    i = int(float(longitude - node_info[3]) * n / (
            float(node_info[2] - node_info[3])))
    j = int(float(latitude - node_info[1]) * n / (
            float(node_info[0] - node_info[1])))

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
                if curr_dist < best_distance:
                    best_node = node
                    best_distance = curr_dist
    return best_node


# Based off its format in the CSV file creates an actual DateTime object
def create_datetime(date_time):
    return datetime(year=int(date_time[0:4]), month=int(date_time[5:7]),
                    day=int(date_time[8:10]), hour=int(date_time[11:13]),
                    minute=int(date_time[14:16]), second=int(date_time[18:]))


# This algorithm takes a street and returns the set of all streets that
# intersect the original street and have been granted a velocity
def find_adjacent(node_tuple, dict_of_streets):
    all_adjacent = set()
    for node in node_tuple[0].distance_connections:
        if (node_tuple[0].id, node.id) in dict_of_streets:
            all_adjacent.add((node_tuple[0], node))
    for node in node_tuple[0].backwards_connections:
        if (node.id, node_tuple[0].id) in dict_of_streets:
            all_adjacent.add((node, node_tuple[0]))
    for node in node_tuple[1].distance_connections:
        if (node_tuple[1].id, node.id) in dict_of_streets:
            all_adjacent.add((node_tuple[1], node))
    for node in node_tuple[1].backwards_connections:
        if (node.id, node_tuple[1].id) in dict_of_streets:
            all_adjacent.add((node, node_tuple[1]))
    return all_adjacent


def get_all_streets(grid_of_nodes):
    all_streets = set()
    for column in grid_of_nodes:
        for region in column:
            for node in region.nodes:
                for connection in node.distance_connections:
                    all_streets.add((node, connection))
    return all_streets


def remove_loop_trips(trips):
    new_trips = []
    for trip in trips:
        if trip.start_node != trip.end_node:
            new_trips.append(trip)
    return new_trips


def remove_extreme_trips(trips):
    new_trips = []
    for trip in trips:
        if float(trip.trip_time) >= 120 and float(trip.trip_time) <= 3600:
            new_trips.append(trip)
    return new_trips


def remove_speed_trips(trips):
    new_trips = []
    for trip in trips:
        try:
            if (float(find_length(trip.nodeList)) / float(trip.trip_time) >= .5
                and float(find_length(trip.nodeList)) /
                    (float(trip.trip_time) <= 30)):
                new_trips.append(trip)
        except(IndexError):
            pass
    return new_trips


def build_dictionary(path):
    dictionary = dict()
    for i in range(len(path) - 1):
        curr_node = path[i]
        next_node = path[i + 1]
        _id = (curr_node.id, next_node.id)
        dictionary[_id] = (curr_node, next_node)
    return dictionary


def find_time(arr):
    if arr == "No Path Found":
        print "COULDN'T FIND PATH"
        return 10000000
    total_time = 0
    for i in range(len(arr) - 1):
        curr_node = arr[i]
        next_node = arr[i + 1]
        total_time += float(curr_node.time_connections[next_node])
    return total_time


def find_length(arr):
    if arr == "No Path Found":
        print "COULDN'T FIND PATH"
        return 10000000
    total_length = 0
    for i in range(len(arr) - 1):
        curr_node = arr[i]
        next_node = arr[i + 1]
        total_length += float(curr_node.distance_connections[next_node])
    return total_length


def build_all_streets_used(path):
    if path == "No Path Found":
        print "COULDN'T FIND PATH"
        return 10000000
    new_set = set()
    for i in range(len(path) - 1):
        curr_node = path[i]
        next_node = path[i + 1]
        new_set.add((curr_node.id, next_node.id))
    return new_set


def get_sorted_unused_streets(all_streets, dict_of_streets):
    unused_streets = []
    for street in all_streets:
        if (street[0].id, street[1].id) not in dict_of_streets:
            all_adjacent = find_adjacent(street, dict_of_streets)
            unused_streets.append((len(all_adjacent), street))
    unused_streets.sort(key=lambda street: street[0])
    unused_streets = unused_streets[::-1]
    return unused_streets


def MITSpeedAlgorithm(read_from, start_time, kill_time, fileName):
    #####################################
    #                                   #
    #                 PART 1:           #
    #          CONDENSE DUPLICATES      #
    #                                   #
    #####################################

    # We will be using a NxN Grid, where each region has a set of nodes
    # to make it easier to seek out nodes
    max_speed = 5  # meters per second
    n = 20
    # Gets all of the nodes
    grid_of_nodes = get_correct_nodes(n, None, None)
    node_info = get_node_range()
    trip_file = csv.reader(open(read_from, 'rb'))
    t_agg = []
    # Each keeps track of distinct trips, so we can filter out duplicates and
    # replace them with a great average trip
    dictionary_cab = dict()
    dictionary_time_agg = dict()
    dictionary_counter = dict()
    dictionary_distance = dict()
    header = True
    for row in trip_file:
        if not header:
            if row[5] > str(kill_time):
                print row[5]
                break
            if row[5] >= str(start_time):
                try:
                    beginnode = find_nodes(float(row[10]), float(row[11]),
                                           grid_of_nodes, node_info, n)
                    end_node = find_nodes(float(row[12]), float(row[13]),
                                          grid_of_nodes, node_info, n)
                except(ValueError):
                    continue
                if beginnode is None or end_node is None:
                    continue
                newEntry = (beginnode.id, end_node.id)
                dictionary_cab[newEntry] = row
                if newEntry in dictionary_time_agg:
                    dictionary_time_agg[newEntry] += float((
                        create_datetime(row[6]) - create_datetime(row[5])
                        ).seconds)
                    dictionary_distance[newEntry] += float(row[9])
                    dictionary_counter[newEntry] += 1
                else:
                    dictionary_time_agg[newEntry] = float((
                        create_datetime(row[6]) - create_datetime(row[5])
                        ).seconds)
                    dictionary_distance[newEntry] = float(row[9])
                    dictionary_counter[newEntry] = 1
        header = False

    # Replaces the single trip with a trip object and adds it to our set of
    # all trips
    for key in dictionary_time_agg:
        # The current trip row
        t = dictionary_cab[key]
        new_time = dictionary_time_agg[key]/dictionary_counter[key]
        new_dist = dictionary_distance[key]/dictionary_counter[key]
        # The new trip array that initializes a trip object
        new_tripList = [t[0], new_time, new_dist, t[10], t[11], t[12], t[13],
                        key[0], key[1], dictionary_counter[key]]
        new_trip = Trip(new_tripList)
        t_agg.append(new_trip)

    print len(t_agg)

    #####################################
    #                                   #
    #                PART 2:            #
    #           REMOVE SHORT/longitude  #
    #                                   #
    #####################################

    # This removes any trip that starts and ends at the same node, as long as
    # extremely short or extremely long trips
    t_agg = remove_loop_trips(t_agg)
    t_agg = remove_extreme_trips(t_agg)

    #####################################
    #                                   #
    #                PART 3:            #
    #            COMPUTE tripS          #
    #                                   #
    #####################################

    for trip in t_agg:
        path = AStar(trip.start_long, trip.start_lat, trip.end_long,
                     trip.end_lat, grid_of_nodes, node_info, n, max_speed)
        trip.nodeList = path

    #####################################
    #                                   #
    #                PART 4:            #
    #           REMOVE FAST/SLOW        #
    #                                   #
    #####################################

    t_agg = remove_speed_trips(t_agg)
    print len(t_agg)

    #############################################
    #############################################
    #                                           #
    #                    PART 5:                #
    #                ITERATIVE PART             #
    #                                           #
    #############################################
    #############################################

    # MIRROR OF PSUEDO CODE: PART 5.1, SET AGAIN = TRUE
    again = True

    # This is a dictionary of sets - give it a streetID (start_node.id,
    # end_node.id) and it will return the set of trips that include that
    # street and O_s
    dict_of_streets = dict()
    time_outer_loop = 0
    time_inner_loop = 0
    iter_outer_loop = 0
    iter_inner_loop = 0

    ##########################################
    #                                        #
    #               PART 5.3:                #
    #              OUTTER LOOP               #
    #                                        #
    ##########################################
    while again:

        # Now the we are out of the Inner Loop, we must reset the times
        # associated with each trip
        print "Outer Loop!"
        start = timeit.default_timer()
        for _id in dict_of_streets:
            tripsWithStreet = dict_of_streets[_id][0]
            # All the streets have the street, so we can pick any one
            random_trip = next(iter(tripsWithStreet))

            # node_tuple[0] = start_node, node_tuple[1] = end_node
            node_tuple = random_trip.node_dict[_id]
            new_time = node_tuple[0].distance_connections[node_tuple[1]] / (
                node_tuple[0].speed_connections[node_tuple[1]])
            node_tuple[0].time_connections[node_tuple[1]] = new_time
        print "End of resetting times"

        # We now have an entirely new set of streets used
        # so we must reset the old dictionary
        dict_of_streets = dict()

        again = False
        rel_error = 0
        # We find new paths based off of the new times we got
        for trip in t_agg:
            path = AStar(trip.start_long, trip.start_lat, trip.end_long,
                         trip.end_lat, grid_of_nodes, node_info, n, max_speed)
            trip.nodeList = path
            trip.node_dict = build_dictionary(path)
            for _id in trip.node_dict:
                if _id in dict_of_streets:
                    dict_of_streets[_id][0].add(trip)
                else:
                    dict_of_streets[_id] = (set(), 0)
                    dict_of_streets[_id][0].add(trip)
            trip.est_time = find_time(path)
            rel_error += abs(trip.est_time - trip.trip_time)/trip.trip_time
        print "End of getting rel_error, finding paths, " + (
            "filling dictionaryand getting streetIDs")

        # Offset Computation
        for _id in dict_of_streets:
            offSet = 0
            for trip in dict_of_streets[_id][0]:
                offSet += (trip.est_time - trip.trip_time) * trip.numtrips
            dict_of_streets[_id] = (dict_of_streets[_id][0], offSet)
        print "End of calculating offset coefficients"
        k = 1.2
        stop = timeit.default_timer()
        time_outer_loop += (stop - start)
        iter_outer_loop += 1
        print stop - start
        ##########################################
        #                                        #
        #               PART 5.3:                #
        #              INNER LOOP                #
        #                                        #
        ##########################################
        print "Inner Loop!"
        # MIRROR OF PSUEDO CODE: PART 5.3, INNER LOOP
        # (KEEP TRACK OF FASTEST SPEED HERE)
        while True:
            start = timeit.default_timer()
            # Recalculates the time with a different ratio
            for _id in dict_of_streets:
                tripsWithStreet = dict_of_streets[_id][0]
                # It doesn't matter what trip we take from this set, as they
                # all include this street
                random_trip = next(iter(tripsWithStreet))
                node_tuple = random_trip.node_dict[_id]
                if dict_of_streets[_id][1] < 0:
                    node_tuple[0].time_connections[node_tuple[1]] = (
                        node_tuple[0].time_connections[node_tuple[1]] * k)
                else:
                    node_tuple[0].time_connections[node_tuple[1]] = (
                        node_tuple[0].time_connections[node_tuple[1]] / k)
            # Figures out what the error would be under these new time
            # constraints
            new_rel_error = 0
            for trip in t_agg:
                etPrime = find_time(trip.nodeList)
                new_rel_error += abs(etPrime - trip.trip_time) / (
                    trip.trip_time)
            # Our new times are more accurate - time to redo everything
            if new_rel_error < rel_error:
                # We are going to have a new fastest speed
                max_speed = -1
                rel_error = new_rel_error
                # Since our new times are better, we ReUpdate the speed based
                # off these new times
                for _id in dict_of_streets:
                    tripsWithStreet = dict_of_streets[_id][0]
                    # It doesn't matter what trip we take from this set
                    # as they all include this street
                    random_trip = next(iter(tripsWithStreet))
                    node_tuple = random_trip.node_dict[_id]
                    new_speed = (
                        node_tuple[0].distance_connections[node_tuple[1]] /
                        node_tuple[0].time_connections[node_tuple[1]])
                    if new_speed > max_speed:
                        max_speed = new_speed
                    node_tuple[0].speed_connections[node_tuple[1]] = new_speed
                again = True
            else:
                # Continue reducing k
                iter_inner_loop += 1
                k = 1 + (k - 1) * .75
                if k < 1.0001:
                    stop = timeit.default_timer()
                    time_inner_loop += (stop - start)
                    print stop - start
                    break

    # TODO: TEST TO MAKE SURE TIMES ARE UP-TO-DATE
    for column in grid_of_nodes:
        for region in column:
            for node in region.nodes:
                for connection in node.time_connections:
                    node.time_connections[connection] = (
                        node.distance_connections[connection] / (
                            node.speed_connections[connection]))

    ##########################################
    #                                        #
    #                 PART 6:                #
    #            UNUSED STREETS              #
    #                                        #
    ##########################################

    print "Outer loop time:"
    print time_outer_loop
    print "Inner loop time:"
    print time_inner_loop
    print "Iterations outer:"
    print iter_outer_loop
    print "Iterations inner:"
    print iter_inner_loop

    # A set of pairs of nodes (start_node, end_node)
    all_streets = get_all_streets(grid_of_nodes)
    unused_streets = get_sorted_unused_streets(all_streets, dict_of_streets)
    prev_len = -1
    # We now set every street in order, averaging the velocity along each
    # street and the times, then assigning it to the usedStreet set
    while True:
        if prev_len == len(unused_streets):
            print prev_len
            for street in unused_streets:
                curr_pair = street[1]
                curr_pair[0].speed_connections[curr_pair[1]] = -1
                curr_pair[0].time_connections[curr_pair[1]] = -1
            break
        prev_len = len(unused_streets)
        for street in unused_streets:
            if street[0] == 0:
                unused_streets = get_sorted_unused_streets(all_streets,
                                                           dict_of_streets)
                break
            curr_pair = street[1]
            all_adjacent = find_adjacent(curr_pair, dict_of_streets)
            all_velocities = 0
            for node_tuple in all_adjacent:
                all_velocities += node_tuple[0].speed_connections[
                    node_tuple[1]]
            if len(all_adjacent) != 0:
                all_velocities /= len(all_adjacent)
            else:
                all_velocities = -1
            curr_pair[0].speed_connections[curr_pair[1]] = all_velocities
            if all_velocities != 0:
                curr_pair[0].time_connections[curr_pair[1]] = (
                    curr_pair[0].distance_connections[curr_pair[1]] / (
                        all_velocities))
            else:
                curr_pair[0].time_connections[curr_pair[1]] = -1
            dict_of_streets[(curr_pair[0].id, curr_pair[1].id)] = (
                curr_pair[0], curr_pair[1])

    ##########################################
    #                                        #
    #                 PART 7:                #
    #            WRITE LINK FILE             #
    #                                        #
    ##########################################

    # Writes all of the pertinent information to a file, so that we can compare
    # it to the link file later and add the time/speed
    link_file = csv.writer(open(fileName, 'wb'))
    headers = ["begin_node_id", "end_node_id", "length", "speed", "time"]
    link_file.writerow(headers)
    for node_tuple in all_streets:
        new_arr = [node_tuple[0].id, node_tuple[1].id,
                   node_tuple[0].distance_connections[node_tuple[1]],
                   node_tuple[0].speed_connections[node_tuple[1]],
                   node_tuple[0].time_connections[node_tuple[1]]]
        link_file.writerow(new_arr)
