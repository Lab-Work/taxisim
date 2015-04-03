from routing.ArcFlagsPreProcess import ArcFlagsPreProcess
from db_functions import db_trip, db_main, db_arc_flags
from datetime import datetime, date, time
from routing import Map

region_size = 4000
# ArcFlagsPreProcess.run(region_size)
arc_flags_map = Map.Map("nyc_map4/nodes.csv", "nyc_map4/links.csv",
                      lookup_kd_size=1, region_kd_size=region_size,
                      limit_bbox=Map.Map.reasonable_nyc_bbox)
arc_flags_map.assign_node_regions()
arc_flags_map.assign_link_arc_flags()
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
trips = db_trip.find_pickup_dt(dt1, dt2)
trips = arc_flags_map.match_trips_to_nodes(trips)
trips1 = trips[:]
print "got trips"
arc_flags_map.routeTrips(trips1, astar_used=True)
print "did first part"
arc_flags_map.routeTrips(trips, arcflags_used=True)

same = True
for i in trips:
	if i.path_links != i.path_links:
		same = False
print same


# go through array and apply no arcflags and no A*, arcflags and A*, arcflags and no A*, A* and no ArcFlagsPreProcess
