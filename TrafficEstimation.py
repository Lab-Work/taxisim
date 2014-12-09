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


def estimate_travel_times(road_map, trips):

    
    unique_trips = match_trips_to_nodes(road_map, trips)
    print "There are " + str(len(unique_trips)) + " unique trips."
    
    
    while(True):    
        print("$$$$$$$$$$$$$$$$$ OUTER LOOP $$$$$$$$$$$$$$$$$$$$$$$$")
        t1 = datetime.now()
        #Determine optimal routes for all trips
        max_speed = road_map.get_max_speed()
        for trip in unique_trips:
            trip.path_links = bidirectional_search(trip.origin_node, trip.dest_node, use_astar=True, max_speed=max_speed)
            #print(str(trip.origin_node.node_id) + " -- > " + str(trip.dest_node.node_id) + " : " + str(len(trip.path_links)) + " hops.")
            
        
        t2 = datetime.now()
        print("Time to route: " + str(t2 - t1))
        
        
        #For each link, we maintain the offset value
        #Which is the number of overestimated minus underestimated travel times
        #Of trips which use this link
        for link in road_map.links:
            link.offset = 0 #Initially we have 0 overestimated and underestimated
        
        prev_l1_error = float('inf')    
        
        eps = .2
        num_iter = 0
        while(eps > .001):
            
            #Step 1 - propose new travel times on the links
            #Links with a positive offset are systematically overestimated - travel times should be decreased
            #Links with a negative offset are systematically underestiamted - travel times should be increased
            for link in road_map.links:
                if(link.offset > 0):
                    link.time = link.time / (1 + eps)
                elif(link.offset < 0):
                    link.time = link.time * (1 + eps)    
    
            
            #Step 2 - Evaluate proposed travel times in terms of L1 error
            #Use routes to predict travel times for trips
            l1_error = 0 #Stores the total prediction error across all trips.  We want to minimize this
            for trip in unique_trips:
                #estimated travel time is the sum of link costs for this trip
                trip.estimated_time = sum([link.time for link in trip.path_links])
                l1_error += abs(trip.estimated_time - trip.time) * trip.num_occurrences
            
            
            
            #Step 3 - compare new and old error
            #If the new is worse, that means we stepped to far, so decrease the step size
            if(prev_l1_error == float('inf')):
                print l1_error
            
            if(l1_error < prev_l1_error):
                #An improvement
                prev_l1_error = l1_error
            else:
                
                #Error increased - we stepped too far
                #Rollback previous changes
                for link in road_map.links:
                    if(link.offset > 0):
                        link.time = link.time * (1 + eps)
                    elif(link.offset < 0):
                        link.time = link.time / (1 + eps)  
                
                #Decrease step size
                eps *= .75
                print ("================= eps=" + str(eps) + " ===================")
                print l1_error
                
                #Rollback previous changes
                
            #Step 4 - compute new offsets on each link
            for trip in unique_trips:
                #update offsets
                if(trip.estimated_time > trip.time):
                    #This trip was overestimated - link offsets increase
                    for link in trip.path_links:
                        link.offset += trip.num_occurrences
                else:
                    #This trip was underrestimated - link offsets decrease
                    for link in trip.path_links:
                        link.offset -= trip.num_occurrences
                        
            num_iter += 1
        t3 = datetime.now()
        print ("GD time: " + str(t3 - t2))
        print ("Num iter " + str(num_iter))
        

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
    trips = load_trips("sample.csv", 10000)
    
    print("We have " + str(len(trips)) + " trips")
    
    print("Loading map")
    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    
   
    
    print("Estimating travel times")
    estimate_travel_times(nyc_map, trips)
    

if(__name__=="__main__"):
    test_on_small_sample()
    
    
    