# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 21:12:41 2015

@author: brian
"""

from db_functions import db_main, db_travel_times
from Map import Map
from datetime import datetime

# Connect to the database
db_main.connect("db_functions/database.conf")
db_travel_times.create_travel_time_table()

# Load map
print("Loading map")
road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")


# Save travel times into DB
start_time = datetime.now()
print("Saving travel times")
db_travel_times.save_travel_times(road_map, start_time)
print("Done")
end_time = datetime.now()
print(str(end_time - start_time))


# Load travel times from the db
start_time = datetime.now()
print("Loading travel times")
db_travel_times.load_travel_times(road_map, start_time)
end_time = datetime.now()
print(str(end_time - start_time))
