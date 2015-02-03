# -*- coding: utf-8 -*-
"""
Created on Mon Feb  2 23:57:13 2015

@author: brian
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Jan 17 14:39:21 2015

@author: brian
"""
from datetime import datetime, timedelta


from traffic_estimation.TrafficEstimation import estimate_travel_times
from routing.Map import Map

from db_functions import db_main, db_trip, db_travel_times


def run_chunk(road_map, time):
    try:
        print("Connecting to db")
        db_main.connect("db_functions/database.conf", retry_interval=10)
        
        print (str(datetime.now()) + " : Analysing " + str(time))
        road_map.unflatten()
    
        t1 = datetime.now()    
        trips = db_trip.find_pickup_dt(time, time + timedelta(hours=1))
        t2 = datetime.now()
        db_main.close()
        print ("Loaded " + str(len(trips)) + " trips after " + str(t2 - t1))
        
    
    
        estimate_travel_times(road_map, trips, max_iter=2, test_set=None, distance_weighting=None, model_idle_time=False, initial_idle_time=0)
        t3 = datetime.now()    
        print (str(t3) + " : Finished estimating traffic for " + str(time) + " after " + str(t3-t2))
        
        
        road_map.save_speeds('tmp_speeds.csv')
    

        #db_main.close()
    except Exception as e:
        print("Failed to estimate traffic for %s : %s" % (str(time), e.message))
        


def do_nothing(road_map, time):
    road_map.unflatten()
    print ("Number of links in map " + str(len(road_map.links)))
    road_map.flatten()
    


def dateRange(start_date, end_date, delta):
	d = start_date
	while(d < end_date):
		yield d
		d += delta




def run_test():
    # Build and prepare the process tree


    print("Loading map")
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    road_map.flatten()  
    d1 = datetime(2012,3,5,hour=9)
    run_chunk(road_map, d1)

