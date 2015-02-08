# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 10:49:39 2015

@author: brian
"""
from datetime import datetime, timedelta
from os import system, remove

from db_functions import db_main, db_travel_times
from routing.Map import Map


def plot_speed(road_map, dt, filename):
    db_travel_times.load_travel_times(road_map, dt)
    title = str(dt)    
    
    road_map.save_speeds(filename + ".csv", num_trips_threshold=1)
    cmd = "Rscript analysis/plot_speeds.R '%s.csv' '%s' '%s'" % (filename, filename, title)
    print(cmd)
    system(cmd)
    remove(filename + ".csv")
    


def plot_many_speeds():
    print("Getting dates")
    db_main.connect("db_functions/database.conf")
    #curs = db_main.execute("select distinct datetime from travel_times where datetime>= '2012-03-04' and datetime < '2012-03-11';")
    #curs = db_main.execute("select distinct datetime from travel_times where datetime>= '2012-06-17' and datetime < '2012-06-24';")

    #dates = [date for (date,) in curs]
    
    #dates = [datetime(2010,6,1,12) + timedelta(days=7)*x for x in range(208)]
    dates = [datetime(2010,1,6,10) + timedelta(days=7)*x for x in range(208)]
    
    dates.sort()    
    print ("There are %d dates" % len(dates))
    
    print ("Loading map.")
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    for date in dates:
        print("running %s" % str(date))
        plot_speed(road_map, date, "analysis/wednesdays/" + str(date) + ".png")