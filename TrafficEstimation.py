# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 14:15:54 2014

@author: Brian Donovan (briandonovan100@gmail.com)
"""
from BiDirectionalSearch import bidirectional_search
from Trip import Trip
from Map import Map

from datetime import datetime
import csv
import math
from multiprocessing import Pool
from functools import partial

import sys, traceback

MAX_SPEED = 30

DW_ABS = 1
DW_REL = 2

DW_GAUSS = 1
DW_LASSO = 2
DW_THRESH = 3



# Computes the average velocity across a series of trips
# computed as total_dist / total_time (longer trips get more weight)
# Params:
    # trips - a list of Trips
# Returns:
    # the average velocity
def compute_avg_velocity(trips):
    s_t = 0.0
    s_d = 0.0
    for trip in trips:
        s_t += trip.time
        s_d += trip.dist
    avg_velocity = s_d / s_t
    
    return avg_velocity



# Computes a trips weight based on how closely the estimated distance and true distance match
# There are several different ways to compute the weight
# Params:
    # distance_weighting - could be None for equal weighting, or a tuple
    # (val_type, kern_type, bandwidth) where:
        # val_type - either DW_ABS or DW_REL. Weighting can be based on absolute or relative error
        # kern_type - either DW_GAUSS, DW_LASSO, or DW_THRESH.  For Gaussian, Lasso, or Threshold weighting
        # bandwidth - (or length-scale) determines the gaussian sdev, lasso width, or threshold for the weighting scheme
    # true_dist - the true reported distance of a trip
    # est_dist - the computed distance of a trip based on the shortest path
def compute_weight(distance_weighting, true_dist, est_dist):
    if(distance_weighting==None):
        return 1
    
    (val_type, kern_type, bandwidth) = distance_weighting
    
    if(val_type==DW_ABS):
        dist_err = est_dist - true_dist
    elif(val_type==DW_REL):
        if(true_dist==0):
            dist_err=1
        else:
            dist_err = (est_dist - true_dist)/ true_dist
    
    if(kern_type==DW_GAUSS):
        return math.e**(-(dist_err/bandwidth)**2)
    elif(kern_type==DW_LASSO):
        return 1 - min(1,abs(dist_err / bandwidth))
    elif(kern_type==DW_THRESH):
        return 1 * (dist_err < bandwidth)
    


# Predicts the duration of a single trip based on its origin, destination, and the state of traffic
# Computes several L1-based error metrics in the process, which measure the prediction accuracy
# It is assumed that the driver will take the shortest path
# This function can be used in a few different contexts, which are given by the parameters route and proposed
# Params:
    # road_map - a Map object which has some travel times on each link
    # trips - a set of Trips that will be routed and predicted
    # route - if True, the shortest paths will be computed (very costly)
        # otherwise, the existing ones will be used (trip.path_links)
    # proposed - if True, link.proposed_time will be used as the cost instead of link.time
    # max_speed - the maximum speed of any Link.  Will be computed if None (a little costly).
        # This is used by the A* heuristic - only important if route=True
    # distance_weighting - the method for computing the weight.  see compute_weight()
# Returns:
    # trip - the same trip that was given as input
    # error - the value of the error metric (which we are trying to minimize)
    # l1_error - the absolute error
    # sum_perc_error - the (positive) percentage error
    # num_trips - the number of trips represented by this one "unique trip"
def predict_trip_time(trip, road_map, route=True, proposed=False, max_speed = None,
                       distance_weighting=None, flatten_after = False):
    try:
        
        if(flatten_after):
            road_map.unflatten()
            trip.unflatten(road_map)
                
        
        error = 0.0
        l1_error = 0.0
        sum_perc_error = 0
        num_trips = 0
        if(route):
            trip.path_links = bidirectional_search(trip.origin_node, trip.dest_node, use_astar=True, max_speed=max_speed)
        
        if(proposed):
            trip.estimated_time = sum([link.proposed_time for link in trip.path_links])
        else:
            trip.estimated_time = sum([link.time for link in trip.path_links])
        
        trip.estimated_dist = sum([link.length for link in trip.path_links])
        
        # This trip may actually represent several duplicate trips (in terms of origin/destination),
        # which may have different true times - the dup_times parameter loops through these 
        for true_time in trip.dup_times:
            l1_error += abs(trip.estimated_time - true_time)
            
    
            # If we are using distance weighting, compute weight with Gaussian kernel
            weight = compute_weight(distance_weighting, trip.dist, trip.estimated_dist)
            error += abs(trip.estimated_time - true_time) * weight
    
                
            sum_perc_error +=  (abs(trip.estimated_time - true_time) / true_time)
            num_trips +=  1
        
        if(flatten_after):
            trip.flatten()
        
        return trip, error, l1_error, sum_perc_error, num_trips
    except:
        raise Exception("".join(traceback.format_exception(*sys.exc_info())))


# Predicts the travel times for many trips, can make use of parallel processing
def predict_trip_times(road_map, trips, route=True, proposed=False, max_speed = None,
                       distance_weighting=None, pool=None):
    if(max_speed==None):
        max_speed = road_map.get_max_speed()
    
    if(pool==None):
        # Create a partial function, which only takes a Trip as input (all of the others are given constants)
        # This makes it easy to use with the map() function
        trip_func = partial(predict_trip_time, road_map=road_map,route=route, proposed=proposed,
                        max_speed=max_speed, distance_weighting=distance_weighting, flatten_after=False)        
        
        # Predict the travel times for all of the trips
        output_list = map(trip_func, trips)

    else:
        # If we are using several cpus, we will use Pool.map() instead
        # However, the Trips and Map must be flattened before they can be sent to worker processes
        print("Flattening everything.")
        for trip in trips:
            trip.flatten()
        road_map.flatten()
        
        print("Splitting")
        
        # Create a partial function, which only takes a Trip as input (all of the others are given constants)
        # This makes it easy to use with the map() function.
        # The trips must be flattened, since they are being sent across processes
        trip_func = partial(predict_trip_time, road_map=road_map,route=route, proposed=proposed,
                        max_speed=max_speed, distance_weighting=distance_weighting, flatten_after=True)         
        
        
        # create the multiprocessing pool to route the Trips in parallel
        
        # Perform the routing with one chunk per CPU
        ideal_chunksize = (len(trips) / pool._processes) + 1
        output_list = pool.map(trip_func, trips, chunksize=ideal_chunksize)
        pool.terminate()
        
        print("Unflattening trips")
        routed_trips = [trip for trip, error, l1_error, sum_perc_error, num_trips in output_list]
        
        # The Pool returns a new copy of the trips - the relevant data must be copied back to the originals
        # The Trip must also be unflattened, for use with the current Map
        for i in xrange(len(trips)):
            trips[i].path_link_ids = routed_trips[i].path_link_ids
            trips[i].estimated_time = routed_trips[i].estimated_time
            trips[i].estimated_dist = routed_trips[i].estimated_dist
            trips[i].unflatten(road_map)
            
    print("Merging outputs")
    total_error = 0.0
    total_l1 = 0.0
    total_perc_error = 0.0
    total_num_trips = 0
    for trip, error, l1_error, sum_perc_error, num_trips in output_list:
        total_error += error
        total_l1 += l1_error
        total_perc_error += sum_perc_error
        total_num_trips += num_trips
    
    avg_error = total_l1 / total_num_trips
    avg_perc_error = total_perc_error / total_num_trips
    return error, avg_error, avg_perc_error
    
            
        
# Compute link offsets based on trip time errors.  Link offsets indicate whether
# this link's travel time should increase or decrease, in order to decrease the 
# error metric.  The sign of link offset should be the same as the sign of the
# derivative of the error function with respect to this link's cost.
# Params:
    # road_map - a Map object
    # unique_trips - a list of Trip objects
    # distance_weighting - the method for computing the weight.  see compute_weight()
def compute_link_offsets(road_map, unique_trips, distance_weighting=None):
    #Start offsets at 0
    for link in road_map.links:
        link.offset = 0
    
    # If we overestimate, increase link offsets
    # If we underestimate, decrease link offsets
    for trip in unique_trips:
        weight = compute_weight(distance_weighting, trip.dist, trip.estimated_dist)       
        
        #print str(use_distance_weighting) + ": " + str(trip.estimated_dist) + " - " + str(trip.dist) + " --> " + str(weight)
        for true_time in trip.dup_times:
            if(trip.estimated_time > true_time):
                for link in trip.path_links:
                    link.offset += weight
            elif(trip.estimated_time < true_time):
                for link in trip.path_links:
                    link.offset -= weight
    




# Uses an iterative algorithm, similar to the one supplied in
# http://www.pnas.org/content/111/37/13290
# in order to estimate link-by link travel times, using many Trips.
# Upon completion, all of the Link objects in road_map.links will have their
# .time attribute modified
# Some diagonstics are also computed in order to assess the model's quality over iterations
# Params:
    # road_map - a Map object, which contains the road geometry
    # trips - a list of Trip objects.
    # max_iter - maximum number of iterations before the experiment ends
    # test_set - an optional hold-out test set to assess how well the model generalizes.
    # distance_weighting - the method for computing the weight.  see compute_weight()
# Returns:
    # iter_avg_errors - A list of the average absolute errors at each iteration
    # iter_perc_errors - A list of average percent errors at each iteration
    # test_avg_errors - A list of average absolute errors on the test set at each iteration
    # test_perc_errors - A list of average percent errors on the test set at each iteration
def estimate_travel_times(road_map, trips, max_iter=20, test_set=None, distance_weighting=None):
    #print("Estimating traffic.  use_distance_weighting=" + str(use_distance_weighting))
    DEBUG = False
    #Collapse identical trips    
    unique_trips = road_map.match_trips_to_nodes(trips)
    #print "There are " + str(len(unique_trips)) + " unique trips."
    
    if(test_set!= None):
        unique_test_trips = road_map.match_trips_to_nodes(test_set)

    # Set initial travel times to average velocity across trips
    avg_velocity = compute_avg_velocity(trips)
    road_map.set_all_link_speeds(avg_velocity)
    
    
    iter_avg_errors = []
    iter_perc_errors = []
    test_avg_errors = []
    test_perc_errors = []
    
    outer_iter = 0
    outer_loop_again = True
    # Outer loop - route all of the trips and produce travel time estimates
    # Will stop once the travel times cannot be improved (or max_iter is reached)
    while(outer_loop_again and outer_iter < max_iter):
        outer_iter += 1
        if(DEBUG):
            print("################## OUTER LOOP " + str(outer_iter) + " ######################")
        

        
        t1 = datetime.now()
        max_speed = road_map.get_max_speed()
        if(DEBUG):
            print("max speed = " + str(max_speed))
        
        # Determine optimal routes for all trips, and predict the travel times
        # This is the most costly part of each iteration
        # l1_error stores the sum of all absolute errors
        error_metric, avg_trip_error, avg_perc_error = predict_trip_times(road_map,
                unique_trips, route=True, distance_weighting=distance_weighting)
        iter_avg_errors.append(avg_trip_error)
        iter_perc_errors.append(avg_perc_error)
        
        # If we have a test set, also evaluate the map on it
        if(test_set != None):
            test_l1_error, test_avg_trip_error, test_perc_error = predict_trip_times(
                road_map, unique_test_trips, route=True)
            test_avg_errors.append(test_avg_trip_error)
            test_perc_errors.append(test_perc_error)
        
        
        #Determine which links need to increase or decrease their travel time
        compute_link_offsets(road_map, unique_trips, distance_weighting=distance_weighting)
        
        
        
        t2 = datetime.now()
        if(DEBUG):
            print("Time to route: " + str(t2 - t1))
        
        eps = .2 # The step size
        outer_loop_again = False # Start optimistic - this might be the last iteration
        # The results of the inner loop may tell us that we need to loop again
        
        # Inner loop - use errors on Trips to refine the Links' travel times
        # We will try making a small step, but will make it even smaller if we overshoot
        # The inner loop stops if we find a step that makes an improvement, or the step size gets too small
        # A small step size will also trigger the outer loop to stop
        while(eps > .0001):
            if(DEBUG):
                print("Taking a step at eps=" + str(eps))
            #Inner Loop Step 1 - propose new travel times on the links
            #Links with a positive offset are systematically overestimated - travel times should be decreased
            #Links with a negative offset are systematically underestiamted - travel times should be increased
            for link in road_map.links:
                if(link.offset > 0):
                    link.proposed_time = link.time / (1 + eps)
                elif(link.offset < 0):
                    link.proposed_time = link.time * (1 + eps)
                else:
                    link.proposed_time = link.time
                
                #Constrain the travel time to a physically realistic value
                link.proposed_time = max(link.proposed_time, link.length/MAX_SPEED)

    
            # Inner Loop Step 2 - Evaluate proposed travel times in terms of L1 error
            # Use routes to predict travel times for trips
            # We do not compute new routes yet (route=False), we use the existing ones
            new_error_metric, avg_trip_error, avg_perc_error = predict_trip_times(
                            road_map, unique_trips, route=False, proposed=True, max_speed=0,
                            distance_weighting=distance_weighting)            
            if(DEBUG):
                print("Old L1 = " + str(error_metric))
                print("New L1 = " + str(new_error_metric))
            
            # Inner Loop Step 3 - Accept the change if it is an improvement
            if(new_error_metric < error_metric):
                # The step decreased the error - accept it!
                for link in road_map.links:
                    link.time = link.proposed_time
                
                # Now that the travel times have changed, we need to route the trips again
                outer_loop_again = True
                break
            else:
                # The step increased the error - reject it!
                # This means we overshot - retry with a smaller step size
                eps *= .75

    #Compute the final error metrics after the last iteration
    error_metric, avg_trip_error, avg_perc_error = predict_trip_times(road_map, unique_trips, route=False, max_speed=0) 
    iter_avg_errors.append(avg_trip_error)
    iter_perc_errors.append(avg_perc_error)
    # If we have a test set, also evaluate the map on it
    if(test_set != None):
        test_l1_error, test_avg_trip_error, test_perc_error = predict_trip_times(road_map, unique_test_trips, route=True)
        test_avg_errors.append(test_avg_trip_error)
        test_perc_errors.append(test_perc_error)
                
    return (iter_avg_errors, iter_perc_errors, test_avg_errors, test_perc_errors)



        

        
        

def load_trips(filename, limit=float('inf')):
    trips = []
    with open(filename, "r") as f:
        reader = csv.reader(f)
        reader.next()
        for line in reader:
            trips.append(Trip(line))
            if(len(trips) >= limit):
                break
        
    return trips
        
        


def test_on_small_sample():
    print("Loading trips")
    trips = load_trips("sample_2.csv", 20000)
    
    print("We have " + str(len(trips)) + " trips")
    
    print("Loading map")
    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    
   
    
    print("Estimating travel times")
    estimate_travel_times(nyc_map, trips)


def plot_unique_trips():
    from matplotlib import pyplot as plt
    trip_lookup = {}
    print("Loading map")
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    
    print("Matching nodes")
    sizes = []
    with open("sample.csv", "r") as f:
        reader = csv.reader(f)
        reader.next()
        for line in reader:
            trip = Trip(line)

            trip.num_occurrences = 1
            trip.origin_node = road_map.get_nearest_node(trip.fromLat, trip.fromLon)
            trip.dest_node = road_map.get_nearest_node(trip.toLat, trip.toLon)
            
            if((trip.origin_node, trip.dest_node) in trip_lookup):
                #Already seen this trip at least once
                trip_lookup[trip.origin_node, trip.dest_node].num_occurrences += 1
            elif trip.origin_node !=None and trip.dest_node != None:
                #Never seen this trip before
                trip_lookup[trip.origin_node, trip.dest_node] = trip
        
            sizes.append(len(trip_lookup))
    plt.plot(range(len(sizes)), sizes)
    plt.xlabel("Inner Loop Iteration")
    plt.ylabel("L1 Error (sec)")
    fig = plt.gcf()
    fig.set_size_inches(20,10)
    fig.savefig('test2png.png',dpi=100)

    
    #Make unique trips into a list and return
    new_trips = [trip_lookup[key] for key in trip_lookup]
    return new_trips

def test_parallel_routing():
    pool = Pool(8)
    
    for cpus in range(1,9):
        
        if(cpus>1):
            pool = Pool(cpus)
        else:
            pool = None
        print("Loading trips")
        trips = load_trips("sample_3.csv", 100)
        
        print("We have " + str(len(trips)) + " trips")
        
        print("Loading map")
        nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
        
        print("Map-matching trips")
        unique_trips = nyc_map.match_trips_to_nodes(trips)    
    
    
        print ("**** Running with " + str(cpus) + " CPUs")
        d1 = datetime.now()
        predict_trip_times(nyc_map, unique_trips, route=True, proposed=False, max_speed = None,
                       distance_weighting=None, pool=pool)
        d2 = datetime.now()
        print ("**** " + str(d2 - d1))
        
        if(pool!=None):
            pool.terminate()
        
        del pool
        del trips
        del nyc_map
        del unique_trips
        del d1
        del d2


if(__name__=="__main__"):
    t1 = datetime.now()
    test_parallel_routing()
    t2 = datetime.now()
    print("TOTAL TIME = " + str(t2 - t1))
    #plot_unique_trips()    
    
    