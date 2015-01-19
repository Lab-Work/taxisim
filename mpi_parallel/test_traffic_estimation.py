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
    db_main.connect("db_functions/database.conf")
    
    print (str(datetime.now()) + " : Estimating traffic for " + str(time))
    road_map.unflatten()

    t1 = datetime.now()    
    trips = db_trip.find_pickup_dt(time, time + timedelta(hours=1))
    t2 = datetime.now()
    print ("Loaded " + str(len(trips)) + " trips after " + str(t2 - t1))

    estimate_travel_times(road_map, trips, max_iter=20, test_set=None, distance_weighting=None, model_idle_time=False, initial_idle_time=0)
    print (str(datetime.now()) + " : Finished estimating traffic for " + str(time))

    db_travel_times.save_travel_times(road_map, time)



def run_test():
    # Build and prepare the process tree 
    t = ProcessTree(6)
    t.prepare()
    
    
    if(MPI.COMM_WORLD.Get_rank()==0):
        d1 = datetime.now()
        print("Loading map")
        road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
        road_map.flatten()            
        
        db_main.connect("db_functions/database.conf")
        db_travel_times.create_travel_time_table()
        datelist = [datetime(year=2012, month=6, day=2, hour=h) for h in range(6)]

        t.map(run_chunk, road_map, datelist)
        t.close()
        
        d2 = datetime.now()
        
        print("Total time : " + str(d2 - d1))
    