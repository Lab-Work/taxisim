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


approx_job_size = {}

# Runs the traffic estimation for a one hour slice of time, and saves the results
# into the database.  This is the function that will be "mapped" by the LoadBalancedProcessTree.
# Params:
    # road_map - a Map object which should already be flattened
    # time - a datetime object representing the starting time of the time slice to be estimated
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
        
    
    
        estimate_travel_times(road_map, trips, max_iter=20, test_set=None,
                              distance_weighting=None, model_idle_time=False, initial_idle_time=0)
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
        
# An iterator function which returns intermediate dates between two datetimes
# Params:
        # start_date - the start date
        # end_date - the end date
        # delta - the step size
def dateRange(start_date, end_date, delta):
	d = start_date
	while(d < end_date):
		yield d
		d += delta

# Populates the global variable approx_job_size with the number of trips for each
# time slice.  It is assumed that timeslices with the same (day_of_week, hour_of_day)
# have approximately the same number of trips.  For example, 9am typically has a lot of trips
# and 4am does not.
def approximate_job_sizes():
    global approx_job_size
    
    print("Approximating job sizes.")
    db_main.connect("db_functions/database.conf", retry_interval=10)
    
    d1 = datetime(2012,6,2)
    d2 = datetime(2012,6,9)
    for d in dateRange(d1, d2, timedelta(hours=1)):
        sql = "SELECT count(*) FROM trip WHERE pickup_datetime >= '%s' AND pickup_datetime < '%s'" % (
                d, d+timedelta(hours=1))
        (jsize,) = db_main.execute(sql).next()
        approx_job_size[d.weekday(), d.hour] = jsize
    
# Approximates the size of a job, given its time.  Only works if approximate_job_sizes()
# has already been called, because it makes use of approx_job_size
def job_size(d):
    global approx_job_size
    return approx_job_size[d.weekday(), d.hour]



#Uses a LoadBalancedProcessTree to compute a lot of traffic estimates in parallel.
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
    
        d1 = datetime(2010,1,1)
        d2 = datetime(2014,1,1)
        datelist = list(dateRange(d1,d2, timedelta(hours=1)))
                
        approximate_job_sizes()

            
        print("Preparing to run %d dates." % len(datelist))
        
        
        t.map(run_chunk, road_map, datelist, job_size)
        t.close()
        
        d2 = datetime.now()
        
        print("Total time : " + str(d2 - d1))
