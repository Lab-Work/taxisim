# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 21:12:41 2015

@author: brian
"""

from traffic_estimation.Trip import Trip
from db_functions import db_main, db_travel_times, db_trip
from routing.Map import Map
from datetime import datetime

from traffic_estimation.TrafficEstimation import estimate_travel_times, load_trips


# Connect to the database
db_main.connect("db_functions/database.conf")



db_travel_times.drop_travel_time_table()
db_travel_times.create_travel_time_table()


# Load map
print("Loading map")
road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")

print("Loading trips")
trips = db_trip.find_pickup_dt('2010-01-02 00:00:00', '2010-01-02 01:00:00')
print (len(trips))


# Get some travel times on the links
print("Estimating travel times")
estimate_travel_times(road_map, trips, max_iter=1, test_set=None, distance_weighting=None, model_idle_time=False)


# Now save these travel times with a bunch of different datetimes
for i in range(20):
    size = db_travel_times.get_travel_time_table_size()
    print str(i) + " ) " + str(size)
    # Save travel times into DB
    start_time = datetime.now()
    print("Saving travel times")
    db_travel_times.save_travel_times(road_map, start_time)
    print("Done")
    end_time = datetime.now()
    print(str(end_time - start_time))

size = db_travel_times.get_travel_time_table_size()
print str(i) + " ) " + str(size)


"""
# Load travel times from the db
start_time = datetime.now()
print("Loading travel times")
db_travel_times.load_travel_times(road_map, start_time)
end_time = datetime.now()
print(str(end_time - start_time))
"""
