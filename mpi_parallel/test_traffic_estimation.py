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
from ProcessTree import ProcessTree


def run_chunk(road_map, time):
    print("Connecting to db")
    db_main.connect("db_functions/database.conf")
    
    print (str(datetime.now()) + " : Estimating traffic for " + str(time))
    road_map.unflatten()

    t1 = datetime.now()    
    trips = db_trip.find_pickup_dt(time, time + timedelta(hours=1))
    t2 = datetime.now()
    print ("Loaded " + str(len(trips)) + " trips after " + str(t2 - t1))

    estimate_travel_times(road_map, trips, max_iter=20, test_set=None, distance_weighting=None, model_idle_time=False, initial_idle_time=0)
    print (str(datetime.now()) + " : Finished estimating traffic for " + str(time))

    t1 = datetime.now()
    db_travel_times.save_travel_times(road_map, time)
    t2 = datetime.now()
    print("Saved travel times after " + str(t2 - t1))


def do_nothing(road_map, time):
    road_map.unflatten()
    print ("Number of links in map " + str(len(road_map.links)))
    road_map.flatten()
    



def run_test():
    # Build and prepare the process tree 
    t = ProcessTree(168, debug_mode=True, batch_size=4)
    t.prepare()
    
    
    if(MPI.COMM_WORLD.Get_rank()==0):
        d1 = datetime.now()
        print("Loading map")
        road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
        road_map.flatten()            
        
        #db_main.connect("db_functions/database.conf")
        #db_travel_times.create_travel_time_table()
        datelist = [datetime(year=2012, month=6, day=24, hour=0) + timedelta(hours=1)*x for x in range(168)]

        t.map(run_chunk, road_map, datelist)
        t.close()
        
        d2 = datetime.now()
        
        print("Total time : " + str(d2 - d1))
    