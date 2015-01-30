# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 15:35:07 2015

@author: brian
"""
from db_functions import db_main, db_trip

from datetime import datetime, timedelta
from routing.Map import Map
from traffic_estimation.Trip import Trip

def analyse_trip_times():
    db_main.connect('db_functions/database.conf')
    
    
    datelist = [datetime(year=2012, month=7, day=8, hour=0) + timedelta(hours=1)*x for x in range(168*3)]
    
    for date in datelist:
        trips = db_trip.find_pickup_dt(date, date+timedelta(hours=1))
        print("%s  :  %d" % (date, len(trips)))


def jfk(lat, lon):
    if(lon > -73.825207 and lon < -73.751907 and
        lat > 40.622843 and lat < 40.665305):
            return True
    return False



def analyse_trip_locations():
    db_main.connect('db_functions/database.conf')
    
    
    datelist = [datetime(year=2012, month=7, day=8, hour=0) + timedelta(hours=1)*x for x in range(168*3)]
    
    nyc_map = Map('nyc_map4/nodes.csv', 'nyc_map4/links.csv', limit_bbox=Map.reasonable_nyc_bbox)
    #nyc_map = Map('nyc_map4/nodes.csv', 'nyc_map4/links.csv')

    
    print [nyc_map.min_lat, nyc_map.max_lat, nyc_map.min_lon, nyc_map.max_lon]

    valid_trips = 0
    bad_region_trips = 0
    jfk_trips = 0
    
    for date in datelist:
        trips = db_trip.find_pickup_dt(date, date+timedelta(hours=1))
        print("%s  :  %d" % (date, len(trips)))
        
        for trip in trips:
            if(trip.isValid()==Trip.VALID):
                valid_trips += 1
                if(nyc_map.get_nearest_node(trip.fromLat, trip.fromLon)==None or
                    nyc_map.get_nearest_node(trip.toLat, trip.toLon)==None):
                    
                    bad_region_trips += 1
                    
                    if(jfk(trip.fromLat, trip.fromLon) or jfk(trip.toLat, trip.toLon)):
                        jfk_trips += 1
                    
                    
                        
        
        print ("Bad trips : %d / %d = %f" % (bad_region_trips, valid_trips, float(bad_region_trips)/valid_trips))
        print ("JFK trips : %d / %d = %f" % (jfk_trips, bad_region_trips, float(jfk_trips)/bad_region_trips))

        
        
            