from db_functions import db_trip, db_main, db_arc_flags
from datetime import datetime, date, time
from routing import Map
import timeit
import sys
from traffic_estimation import plot_estimates
from routing import partition_graph
from routing import DijkstrasAlgorithm


def region_graph_generator(road_map):
	partition_graph.output_clusters(road_map, road_map.total_region_count, 10, "cluster.csv")
	partition_graph.plot_map("cluster.csv", "output")


def createMap(region_size):

	db_main.connect("db_functions/database.conf")


	d = date(2011, 3, 2)
	t = time(19, 40)
	t1 = time(20, 00)
	dt1 = datetime.combine(d, t)
	dt2 = datetime.combine(d, t1)

	trips_arc = db_trip.find_pickup_dt(dt1, dt2)
	
	region_size = region_size/4
	approxSize = len(trips_arc)/region_size

	arc_flags_map = Map.Map("nyc_map4/nodes.csv", "nyc_map4/links.csv",
		                      lookup_kd_size=1, region_kd_size=approxSize,
		                      limit_bbox=Map.Map.reasonable_nyc_bbox)
	arc_flags_map.assign_node_regions()

	
	trips_arc = arc_flags_map.match_trips_to_nodes(trips_arc)


	for trip in trips_arc:
		trip.origin_node.trip_weight += 1
		trip.dest_node.trip_weight += 1

		

	arc_flags_map.build_kd_trees(split_weights=True)
	arc_flags_map.assign_node_regions()


	# same_region = 0
	# for trip in trips_arc:
	# 	if trip.origin_node.region_id == trip.dest_node.region_id:
	# 		same_region+=1

	# print "number of trips in same region are: %d out of %d \n" % (same_region, len(trips_arc))

	region_graph_generator(arc_flags_map)

	db_main.close()

	# region_to_trips = {}
	# for node in arc_flags_map.nodes:
	# 	if node.region_id in region_to_trips:
	# 		region_to_trips[node.region_id] += node.trip_weight
	# 	else:
	# 		region_to_trips[node.region_id] = node.trip_weight
	# for i in region_to_trips:
	# 	print "Region %d: %d trips" % (i, region_to_trips[i])

	return arc_flags_map

# createMap(100)

