# -*- coding: utf-8 -*-
"""
Created on Sat Jan 17 14:39:21 2015

@author: brian
"""
from datetime import datetime, timedelta

from mpi4py import MPI


from traffic_estimation.TrafficEstimation import estimate_travel_times
from routing.Map import Map

from db_functions import db_main, db_trip, db_travel_times
from LoadBalancedProcessTree import LoadBalancedProcessTree


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
        
    
    
        estimate_travel_times(road_map, trips, max_iter=20, test_set=None, distance_weighting=None, model_idle_time=False, initial_idle_time=0)
        t3 = datetime.now()    
        print (str(t3) + " : Finished estimating traffic for " + str(time) + " after " + str(t3-t2))
    
        db_main.connect("db_functions/database.conf", retry_interval=10)
        t1 = datetime.now()
        db_travel_times.save_travel_times(road_map, time)
        t2 = datetime.now()
        print("Saved travel times after " + str(t2 - t1))
        db_main.close()
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

    num_cpus = MPI.COMM_WORLD.Get_size()
    t = LoadBalancedProcessTree(num_cpus, debug_mode=True)
    t.prepare()
    
    
    if(MPI.COMM_WORLD.Get_rank()==0):
        d1 = datetime.now()
        print("Loading map")
        road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
        road_map.flatten()            
        
        #db_main.connect("db_functions/database.conf")
        #db_travel_times.create_travel_time_table()
    
        d1 = datetime(2012,1,1)
        d2 = datetime(2014,1,1)
        datelist = list(dateRange(d1,d2, timedelta(hours=1)))        
        
        
        t.map(run_chunk, road_map, datelist)
        t.close()
        
        d2 = datetime.now()
        
        print("Total time : " + str(d2 - d1))
