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
from matplotlib import pyplot as plt
import math

MAX_SPEED = 30

# Uses a Map object to match a list of Trips to their nearest intersections (Nodes)
# Upon completion, each trip will have .origin_node and .dest_node attributes
# For efficiency, duplicates (some orig/dest) are also removed - although the Trips
# are edited "in place", this function still returns a subset of them.  The trip.dup_times
# attribute is set, which
# Params:
    # road_map - a Map object, which supplies the road geometry
    # trips - a list of Trip objects to be map-matched
def match_trips_to_nodes(road_map, trips):
    trip_lookup = {} # lookup a trip by origin, destination nodes
    
    #First find the nearest origin/destination nodes for each trip
    #We will also find duplicate trips (same origin,destination nodes)
    for trip in trips:
        if(trip.isValid() == Trip.VALID):
            trip.num_occurrences = 1
            trip.origin_node = road_map.get_nearest_node(trip.fromLat, trip.fromLon)
            trip.dest_node = road_map.get_nearest_node(trip.toLat, trip.toLon)
            
            if((trip.origin_node, trip.dest_node) in trip_lookup):
                #Already seen this trip at least once
                trip_lookup[trip.origin_node, trip.dest_node].num_occurrences += 1
                trip_lookup[trip.origin_node, trip.dest_node].dup_times.append(trip.time)
                trip.dup_times = None
            elif trip.origin_node !=None and trip.dest_node != None:
                #Never seen this trip before
                trip_lookup[trip.origin_node, trip.dest_node] = trip
                trip_lookup[trip.origin_node, trip.dest_node].dup_times = [trip.time]

    
    #Make unique trips into a list and return
    new_trips = [trip_lookup[key] for key in trip_lookup]
    return new_trips


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
        s_d += trip.dist * 1609.34
    avg_velocity = s_d / s_t
    
    return avg_velocity




# Predicts the duration of trips, based on their origin, destination, and the state of traffic
# Computes several L1-based error metrics in the process, which measure the prediction accuracy
# It is assumed that the driver will take the shortest path
# This function can be used in a few different contexts, which are given by the route and proposed parameters
# Params:
    # road_map - a Map object which has some travel times on each link
    # trips - a set of Trips that will be routed and predicted
    # route - if True, the shortest paths will be computed (very costly)
        # otherwise, the existing ones will be used (trip.path_links)
    # proposed - if True, link.proposed_time will be used as the cost instead of link.time
    # max_speed - the maximum speed of any Link.  Will be computed if None (a little costly).
        # This is used by the A* heuristic - only important if route=True
    # use_distance_weighting - Changes the error metric.  If True, trips which disagree
        # on distance and estimated_distance get a lower weight in the error metric
    # distance_bandwidth - Used if distance_weighting=True.  We use a Gaussian kernel
        # to weight trips, and this value determines the standard deviation.
# Returns:
    # l1_error - the value of the error metric (which we are trying to minimize)
    # avg_trip_error - average absolute error across all trips
    # avg_perc_error - average percent error across all trips
def predict_trip_times(road_map, trips, route=True, proposed=False, max_speed = None,
                       use_distance_weighting=False, distance_bandwidth=800.00):
    if(max_speed==None):
        max_speed = road_map.get_max_speed()
    
    error = 0.0
    l1_error = 0.0
    avg_perc_error = 0
    num_trips = 0
    for trip in trips:
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
            
            if(use_distance_weighting):
                #If we are using distance weighting, compute weight with Gaussian kernel
                weight = math.e**(-((trip.estimated_dist - trip.dist)/distance_bandwidth)**2)
                error += abs(trip.estimated_time - true_time) * weight
            else:
                #If we are not using distance weighting, just use the l1 error
                error = l1_error
                
            avg_perc_error +=  (abs(trip.estimated_time - true_time) / true_time)
            num_trips +=  1
    
    avg_perc_error /= num_trips
    avg_trip_error = l1_error / num_trips
    return error, avg_trip_error, avg_perc_error
        
# Compute link offsets based on trip time errors.  Link offsets indicate whether
# this link's travel time should increase or decrease, in order to decrease the 
# error metric.  The sign of link offset should be the same as the sign of the
# derivative of the error function with respect to this link's cost.
# Params:
    # road_map - a Map object
    # unique_trips - a list of Trip objects
    # use_distance_weighting - Changes the error metric.  If True, trips which disagree
        # on distance and estimated_distance get a lower weight in the error metric
    # distance_bandwidth - Used if distance_weighting=True.  We use a Gaussian kernel
        # to weight trips, and this value determines the standard deviation.
def compute_link_offsets(road_map, unique_trips, use_distance_weighting=False,
                            distance_bandwidth=800.00):
    #Start offsets at 0
    for link in road_map.links:
        link.offset = 0
    
    # If we overestimate, increase link offsets
    # If we underestimate, decrease link offsets
    for trip in unique_trips:
        if(use_distance_weighting):
            # If we are using distance weighting, this trip's weight depends on
            # the agreement of its distance and estimated distance
            weight = math.e**(-((trip.estimated_dist - trip.dist)/distance_bandwidth)**2)
        else:
            weight = 1        
        
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
    # use_distance_weighting - Changes the error metric.  If True, trips which disagree
        # on distance and estimated_distance get a lower weight in the error metric
    # distance_bandwidth - Used if distance_weighting=True.  We use a Gaussian kernel
        # to weight trips, and this value determines the standard deviation.
# Returns:
    # iter_avg_errors - A list of the average absolute errors at each iteration
    # iter_perc_errors - A list of average percent errors at each iteration
    # test_avg_errors - A list of average absolute errors on the test set at each iteration
    # test_perc_errors - A list of average percent errors on the test set at each iteration
def estimate_travel_times(road_map, trips, max_iter=20, test_set=None, use_distance_weighting=False, 
                          distance_bandwidth=800.00):
    print("Estimating traffic.  use_distance_weighting=" + str(use_distance_weighting))
    DEBUG = False
    #Collapse identical trips    
    unique_trips = match_trips_to_nodes(road_map, trips)
    #print "There are " + str(len(unique_trips)) + " unique trips."
    
    if(test_set!= None):
        unique_test_trips = match_trips_to_nodes(road_map, test_set)

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
                unique_trips, route=True, use_distance_weighting=use_distance_weighting,
                distance_bandwidth=distance_bandwidth)
        iter_avg_errors.append(avg_trip_error)
        iter_perc_errors.append(avg_perc_error)
        
        # If we have a test set, also evaluate the map on it
        if(test_set != None):
            test_l1_error, test_avg_trip_error, test_perc_error = predict_trip_times(
                road_map, unique_test_trips, route=True)
            test_avg_errors.append(test_avg_trip_error)
            test_perc_errors.append(test_perc_error)
        
        
        #Determine which links need to increase or decrease their travel time
        compute_link_offsets(road_map, unique_trips)
        
        
        
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
                            use_distance_weighting=use_distance_weighting,
                            distance_bandwidth=distance_bandwidth)            
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



if(__name__=="__main__"):
    t1 = datetime.now()
    test_on_small_sample()
    t2 = datetime.now()
    print("TOTAL TIME = " + str(t2 - t1))
    #plot_unique_trips()    
    
    