# -*- coding: utf-8 -*-
"""
Created on Sat Jan 17 14:39:21 2015

@author: brian
"""

from TrafficEstimation import estimate_travel_times, load_trips
from datetime import datetime

def run_chunk(road_map, (infile, outdate)):
    d = datetime.now()
    print (str(datetime.now()) + " : Running " + str((infile, outdate)))
    road_map.unflatten()

    trips = load_trips(filename)


    estimate_travel_times(road_map, trips, max_iter=20, test_set=None, distance_weighting=None, model_idle_time=False, initial_idle_time=0)
    print (str(datetime.now()) + " : Finished " + str((infile, outdate)))
