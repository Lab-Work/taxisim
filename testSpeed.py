from routing.ArcFlagsPreProcess import ArcFlagsPreProcess
from db_functions import db_trip, db_main, db_arc_flags
from datetime import datetime, date, time
from routing import Map
import timeit
import copy
import sys
from traffic_estimation import plot_estimates
from routing import partition_graph
from routing import DijkstrasAlgorithm
import cluster_kd
# from DijkstrasAlgorithm import DijkstrasAlgorithm




def draw_graphs(trips_none, trips_arc, arc_flags_map, i):
	end_region_id = trips_none[i].path_links[-1].connecting_node.region_id
	start_region_id = trips_none[i].path_links[0].origin_node.region_id 
	pace_dict = {}
	for link in arc_flags_map.links:
		pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5
	for link in trips_none[i].path_links:
		pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5
	for link in trips_arc[i].path_links:
		if pace_dict[(link.origin_node_id, link.connecting_node_id)] == 5:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = 2
		else:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = 0
	plot_estimates.plot_speed(arc_flags_map, "Correct Path" + str(i), "Correct Path" + str(i), pace_dict)

	pace_dict = {}

	for link in arc_flags_map.links:
		if link.forward_arc_flags_vector[end_region_id] == False:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5
		else:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5
	
	plot_estimates.plot_speed(arc_flags_map, "Forward arcs" + str(i), "Forward arcs" + str(i), pace_dict)

	pace_dict = {}
	for link in arc_flags_map.links:
		if link.backward_arc_flags_vector[start_region_id] == True:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5
		else:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5

	plot_estimates.plot_speed(arc_flags_map, "Backward arcs" + str(i), "Backward arcs" + str(i), pace_dict)




def run_test(region_size, preprocess=False):
	if preprocess:
		start = timeit.default_timer()
		ArcFlagsPreProcess.run(region_size)
		stop = timeit.default_timer()
		print "The time for preprocessing was " + str(stop-start)

	# arc_flags_map = Map.Map("nyc_map4/nodes.csv", "nyc_map4/links.csv",
	#                       lookup_kd_size=1, region_kd_size=region_size,
	#                       limit_bbox=Map.Map.reasonable_nyc_bbox)
	# arc_flags_map.assign_node_regions()

	arc_flags_map = cluster_kd.createMap(region_size)
	arc_flags_map.assign_link_arc_flags()

	###########################
	# arc_flags_map.save_as_csv("nodeRegions.csv", "linkRegions.csv")
	###########################

	print "loaded map"
	db_main.connect("db_functions/database.conf")
	d = datetime(2012,3,5,2)
	db_arc_flags.load_arc_flags(arc_flags_map, d)
	print "loaded arcflags"


	d = date(2011, 3, 2)
	t = time(19, 40)
	t1 = time(20, 00)
	dt1 = datetime.combine(d, t)
	dt2 = datetime.combine(d, t1)

	trips_arc = db_trip.find_pickup_dt(dt1, dt2)
	trips_arc = arc_flags_map.match_trips_to_nodes(trips_arc)

		
	trips_star = db_trip.find_pickup_dt(dt1, dt2)
	trips_star = arc_flags_map.match_trips_to_nodes(trips_star)

	trips_none = db_trip.find_pickup_dt(dt1, dt2)
	trips_none = arc_flags_map.match_trips_to_nodes(trips_none)

	trips_both = db_trip.find_pickup_dt(dt1, dt2)
	trips_both = arc_flags_map.match_trips_to_nodes(trips_both)

	db_main.close()

	same = True
	# for i in range(len(trips_star)):
	# 	if trips_star[i].fromLon != trips_arc[i].fromLon:
	# 		same = False
	# 	if trips_star[i].toLon != trips_arc[i].toLon:
	# 		same = False
	# print "the two trips are the same: " + str(same)

	print "got " + str(len(trips_arc)) + " trips"

	# start = timeit.default_timer()
	# arc_flags_map.routeTrips(trips_none)
	# stop = timeit.default_timer()
	# print "Computed trips using normal dijkstras in " + str(stop-start)

	# start = timeit.default_timer()
	# arc_flags_map.routeTrips(trips_star, astar_used=True)
	# stop = timeit.default_timer()
	# print "Computed trips using Astar in " + str(stop-start)

	# start = timeit.default_timer()
	# arc_flags_map.routeTrips(trips_arc, arcflags_used=True)
	# stop = timeit.default_timer()
	# print "Computed trips using arc_flags in " + str(stop-start)

	start = timeit.default_timer()
	arc_flags_map.routeTrips(trips_both, arcflags_used=True, astar_used=True)
	stop = timeit.default_timer()
	print "Computed trips using arc_flags and a_star in " + str(stop-start)

	failed_trips = []
	same = True
	for i in range(len(trips_arc)):
		if trips_none[i].path_links != trips_star[i].path_links:
			same = False
		if trips_none[i].path_links != trips_both[i].path_links:
			same = False
		if trips_none[i].path_links != trips_arc[i].path_links:
			time1 = 0
			time2 = 0
			draw_graphs(trips_none, trips_arc, arc_flags_map, i)
			for link in trips_none[i].path_links:
				time1 += link.time
			for link in trips_arc[i].path_links:
				time2 += link.time
			print "The time for none is: " + str(time1) + " The time for the arcs_flags is: " + str(time2)
			failed_trips.append(trips_none[i])
			same = False
	# print "The four trips are the same: " + str(same)
	print "\n\n\n\n"
	return failed_trips, arc_flags_map


def region_graph_generator(road_map):
	partition_graph.output_clusters(road_map, road_map.total_region_count, 10, "cluster.csv")
	partition_graph.plot_map("cluster.csv", "output")


def draw_arc_flags(road_map, region, forward_arc_flags = True):
	pace_dict = {}
	for link in road_map.links:
		if forward_arc_flags == True:
			vector = link.forward_arc_flags_vector
		else:
			vector = link.backward_arc_flags_vector
		if vector[region] == False:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5
		else:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5
	if forward_arc_flags:
		plot_estimates.plot_speed(road_map, "Forward arcs temp", "Forward arcs temp", pace_dict)
	else:
		plot_estimates.plot_speed(road_map, "Backward arcs temp", "Backwards arcs temp", pace_dict)




run_test(1000, False)
# arr = [4000, 2000, 1000, 500, 250, 125]
# for i in arr:
# 	run_test(i, True)



def run_independent(failed_trip, i):
	arc_flags_map = Map.Map("nyc_map4/nodes.csv", "nyc_map4/links.csv",
		                      lookup_kd_size=1, region_kd_size=1000,
		                      limit_bbox=Map.Map.reasonable_nyc_bbox)
	arc_flags_map.assign_node_regions()
	arc_flags_map.assign_link_arc_flags()
	# region_graph_generator(arc_flags_map)

	db_main.connect("db_functions/database.conf")

	failed_trip.path_links = []
	trips = [failed_trip]
	
	trips_arc = arc_flags_map.match_trips_to_nodes(trips)

	# originNode = arc_flags_map.nodes_by_id[trips_arc[0].origin_node_id]
	# destNode = arc_flags_map.nodes_by_id[trips_arc[0].dest_node_id]

	originNode = trips_arc[0].origin_node
	destNode = trips_arc[0].dest_node
	

	boundary_nodes = arc_flags_map.get_region_boundary_nodes(originNode.region_id)
	DijkstrasAlgorithm.DijkstrasAlgorithm.independent_dijkstra(boundary_nodes, arc_flags_map)
	DijkstrasAlgorithm.DijkstrasAlgorithm.set_arc_flags(arc_flags_map, boundary_nodes[0].region_id)

	boundary_nodes = arc_flags_map.get_region_boundary_nodes(destNode.region_id)
	DijkstrasAlgorithm.DijkstrasAlgorithm.independent_dijkstra(boundary_nodes, arc_flags_map)
	DijkstrasAlgorithm.DijkstrasAlgorithm.set_arc_flags(arc_flags_map, boundary_nodes[0].region_id)

	draw_arc_flags(arc_flags_map, destNode.region_id, True)
	draw_arc_flags(arc_flags_map, originNode.region_id, False)

	pace_dict = {}
	arc_flags_map.routeTrips(trips_arc, arcflags_used=True)
	for link in arc_flags_map.links:
		pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5
	for link in trips_arc[0].path_links:
		pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5

	plot_estimates.plot_speed(arc_flags_map, "Independent" + str(i), "Independent" + str(i), pace_dict)



def get_boundary_nodes(failed_trip, region_id):
	boundaries = []
	for link in failed_trip.path_links:
		# print "(" + str(link.origin_node.region_id) + ", " + str(link.origin_node.is_boundary_node) + ")"
		if link.origin_node.is_boundary_node == True and link.origin_node.region_id == region_id:
			boundaries.append(link.origin_node)
	if link.connecting_node.is_boundary_node == True and link.connecting_node.region_id == region_id:
			boundaries.append(link.connecting_node)
	return boundaries




def graph_arc_flags(node, arc_flags_map, i):
	arc_flags_map.assign_link_arc_flags()
	DijkstrasAlgorithm.DijkstrasAlgorithm.independent_dijkstra([node], arc_flags_map)
	DijkstrasAlgorithm.DijkstrasAlgorithm.set_arc_flags(arc_flags_map, failed_trips[i].path_links[0].origin_node.region_id)

	pace_dict = {}
	for link in arc_flags_map.links:
		if link.backward_arc_flags_vector[failed_trips[i].path_links[0].origin_node.region_id] == False:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5
		else:
			pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5

	plot_estimates.plot_speed(arc_flags_map, "Boundary Nodes" + str(i), "Boundary Nodes" + str(i), pace_dict)





# failed_trips, arc_flags_map = run_test(1000, False)

# for i in range(len(failed_trips)):
# 	boundaries = get_boundary_nodes(failed_trips[i], failed_trips[i].path_links[0].origin_node.region_id)
# 	for node in boundaries:
# 		graph_arc_flags(node, arc_flags_map, i)
# 	graph_arc_flags(failed_trips[i].path_links[0].origin_node, arc_flags_map, 1000)



	# run_independent(failed_trips[i], i)












