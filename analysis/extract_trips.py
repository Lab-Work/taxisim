from routing.Map import Map
from db_functions import db_main, db_trip


from datetime import datetime
import csv

def extract_trips():
    print("Loading map")
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    db_main.connect("db_functions/database.conf")
    
    
    
    dt1 = datetime(2012,6,1,12)
    dt2 = datetime(2012,6,1,12,30)
    print("Loading trips")
    trips = db_trip.find_pickup_dt(dt1, dt2)
    
    
    print("Matching trips")
    samp = trips[1:100]
    new_samp = road_map.match_trips_to_nodes(samp)
    road_map.routeTrips(new_samp)
    
    with open('trip_links.csv', 'w') as f:
        w = csv.writer(f)
        w.writerow(['trip_id', 'from_lat','from_lon','to_lat','to_lon'])
        for i in range(len(new_samp)):
            print i
            if(samp[i].path_links !=None):
                for link in samp[i].path_links:
                    w.writerow([i, link.origin_node.lat, link.origin_node.long, link.connecting_node.lat, link.connecting_node.long])
    


