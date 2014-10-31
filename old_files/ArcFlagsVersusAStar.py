from Node import get_correct_nodes, get_node_range
import ArcFlags
import AStar
from Trip import Trip
import timeit
import csv

# This file is made for debugging purposes - meant to compare ArcFlags to A*
# in terms of accuracy

read_from = "../data_chron/FOIL2013/trip_04.csv"
n = 20
trip_file = csv.reader(open(read_from, 'rb'))
i = 0
# Holds a set of random trips
all_trips = []
header = True
# Get 20000 trips
for t in trip_file:
    if header:
        # First row is just descriptions of data, not data at all
        header = False
        continue
    if i > 20000:
        break
    i += 1
    # This list is used to initialize a Trip object
    new_trip_list = [t[0], t[8], t[9], float(t[10]), float(t[11]),
                     float(t[12]), float(t[13]), -1, -1, 1]
    new_trip = Trip(new_trip_list)
    all_trips.append(new_trip)
grid_arcs = get_correct_nodes(n, "speeds_per_hour/0_0",
                              "ArcFlags/20Regions0_0.csv")
grid_a_star = get_correct_nodes(n, "speeds_per_hour/0_0", None)
node_info = get_node_range(grid_a_star)
max_speed = 0
# Iterates through every edge to find te fastest speed
for column in grid_a_star:
    for region in column:
        for node in region.nodes:
            for connection in node.speed_connections:
                if node.speed_connections[connection] > max_speed:
                    max_speed = node.speed_connections[connection]
all_trips_arcs = []
all_trips_star = []
# Get all the AStar trips
# Get all the arcFlag trips and the time for both
start = timeit.default_timer()
for a_trip in all_trips:
    all_trips_arcs.append(ArcFlags(a_trip.start_long, a_trip.start_lat,
                          a_trip.end_long, a_trip.end_lat, grid_arcs,
                          node_info, n, max_speed))
stop = timeit.default_timer()
print stop - start
i = 0
start = timeit.default_timer()
for a_trip in all_trips:
    all_trips_star.append(AStar(a_trip.start_long, a_trip.start_lat,
                          a_trip.end_long, a_trip.end_lat, grid_a_star,
                          node_info, n, max_speed))
stop = timeit.default_timer()
print stop - start

trip_file = csv.writer(open("debugging_tools/aFVAS.csv", 'wb'))
headers = ["arcOrStar", "tripNumber", "start_lat", "start_long", "end_lat",
           "end_long"]
trip_file.writerow(headers)

# Compares the trips to ensure they are all the same
for i in range(len(all_trips_arcs)):
    curr_trip_arc = ""
    curr_trip_star = ""
    print i
    sum_star = 0
    sum_arcs = 0
    # Writes to CSV files so we can use R later to print a graph
    for j in range(len(all_trips_arcs[i]) - 1):
        curr_arc = all_trips_arcs[i][j]
        next_arc = all_trips_arcs[i][j + 1]
        sum_arcs += curr_arc.time_connections[next_arc]
        new_row = ["Arc", i, curr_arc.lat, curr_arc.long, next_arc.lat,
                   next_arc.long]
        trip_file.writerow(new_row)
    for j in range(len(all_trips_star[i]) - 1):
        curr_star = all_trips_star[i][j]
        next_star = all_trips_star[i][j + 1]
        sum_star += curr_star.time_connections[next_star]
        new_row = ["Star", i, curr_star.lat, curr_star.long, next_star.lat,
                   next_star.long]
        trip_file.writerow(new_row)
    print sum_arcs
    print sum_star
