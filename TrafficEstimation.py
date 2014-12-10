# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 14:15:54 2014

@author: brian
"""
from BiDirectionalSearch import bidirectional_search
from Trip import Trip
from Map import Map
from datetime import datetime
import csv
from math import log
from matplotlib import pyplot as plt

MAX_SPEED = 30

# Uses a Map object to match a list of Trips to their nearest intersections (Nodes)
# Upon completion, each trip will have .origin_node and .dest_node attributes
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
            elif trip.origin_node !=None and trip.dest_node != None:
                #Never seen this trip before
                trip_lookup[trip.origin_node, trip.dest_node] = trip

    
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



# Uses an iterative algorithm, similar to the one supplied in
# http://www.pnas.org/content/111/37/13290
# in order to estimate link-by link travel times, using many Trips.
# Upon completion, all of the Link objects in road_map.links will have their
# .time attribute modified
# Params:
    # road_map - a Map object, which contains the road geometry
    # trips - a list of Trip objects
def estimate_travel_times(road_map, trips, max_iter=20):

    #Collapse identical trips    
    unique_trips = match_trips_to_nodes(road_map, trips)
    print "There are " + str(len(unique_trips)) + " unique trips."

    #set initial travel times to average velocity across trips
    avg_velocity = compute_avg_velocity(trips)
    road_map.set_all_link_speeds(avg_velocity)
    
    
    iter_errors = []
    outer_iter = 0
    outer_loop_again = True
    #Outer loop - route all of the trips and produce travel time estimates
    #Will stop once the travel times cannot be improved (or max_iter is reached)
    while(outer_loop_again and outer_iter < max_iter):
        outer_iter += 1
        road_map.save_speeds('tmp_speeds/iteration_' + str(outer_iter) + '.csv')
        print("################## OUTER LOOP " + str(outer_iter) + " ######################")
        
        #For each link, we maintain the offset value
        #Which is the number of overestimated minus underestimated travel times
        #Of trips which use this link
        for link in road_map.links:
            link.offset = 0 #Initially we have 0 overestimated and underestimated
            link.proposed_time = link.time
        
        
        t1 = datetime.now()
        max_speed = road_map.get_max_speed()
        print("max speed = " + str(max_speed))
        
        l1_error = 0
        #Determine optimal routes for all trips - also determine travel time errors and Link offsets
        for trip in unique_trips:
            trip.path_links = bidirectional_search(trip.origin_node, trip.dest_node, use_astar=True, max_speed=max_speed)
            #Estimated trip time is the sum of link travel costs            
            estimated_time = sum([link.time for link in trip.path_links])
            if(estimated_time > trip.time):
                for link in trip.path_links:
                    link.offset += trip.num_occurrences
            elif(estimated_time < trip.time):
                for link in trip.path_links:
                    link.offset -= trip.num_occurrences
            
            #compute the overall absolute error for all trips - note that trips are weighted by their number of occurrences
            l1_error += abs(estimated_time - trip.time) * trip.num_occurrences
        
        iter_errors.append(l1_error)
        t2 = datetime.now()
        print("Time to route: " + str(t2 - t1))
        
        eps = .2 # The step size
        outer_loop_again = False # Start optimistic - this might be the last iteration
        # The results of the inner loop may tell us that we need to loop again
        
        # Inner loop - use errors on Trips to refine the Links' travel times
        # We will try making a small step, but will make it even smaller if we overshoot
        # The inner loop stops if we find a step that makes an improvement, or the step size gets too small
        # A small step size will also trigger the outer loop to stop
        while(eps > .0001):
            print("Taking a step at eps=" + str(eps))
            #Inner Loop Step 1 - propose new travel times on the links
            #Links with a positive offset are systematically overestimated - travel times should be decreased
            #Links with a negative offset are systematically underestiamted - travel times should be increased
            for link in road_map.links:
                if(link.offset > 0):
                    link.proposed_time = link.time / (1 + eps)
                elif(link.offset < 0):
                    link.proposed_time *= (1 + eps)
                
                #Constrain the travel time to a physically realistic value
                link.proposed_time = max(link.proposed_time, link.length/MAX_SPEED)

    
            # Inner Loop Step 2 - Evaluate proposed travel times in terms of L1 error
            # Use routes to predict travel times for trips
            new_l1_error = 0 #Stores the total prediction error across all trips. We want to minimize this
            for trip in unique_trips:
                #estimated travel time is the sum of link costs for this trip
                estimated_time = sum([link.proposed_time for link in trip.path_links])
                new_l1_error += abs(estimated_time - trip.time) * trip.num_occurrences
            
            print("Old L1 = " + str(l1_error))
            print("New L1 = " + str(new_l1_error))
            
            # Inner Loop Step 3 - Accept the change if it is an improvement
            if(new_l1_error < l1_error):
                # The step decreased the error - accept it!
                print("Accepting!")
                for link in road_map.links:
                    link.time = link.proposed_time
                
                # Now that the travel times have changed, we need to route the trips again
                outer_loop_again = True
                break
            else:
                # The step increased the error - reject it!
                # This means we overshot - retry with a smaller step size
                eps *= .75
                print("Stepped too far. Decreasing eps...")
                
            
            

    plt.plot(iter_errors)
    plt.savefig("travel_time_errors.png")
        
    road_map.save_speeds('tmp_speeds/iteration_' + str(outer_iter + 1) + '.csv')



        
        

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
    
    