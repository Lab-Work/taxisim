# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 10:49:39 2015

@author: brian
"""
from datetime import datetime, timedelta
from os import system, remove, path

from db_functions import db_main, db_travel_times
from routing.Map import Map
from 




#Splits a range of numbers into segments - useful for splitting data for parallel processing
#Size - the number of elements to be split
#numSegments - the number of segments to split them into
def splitRange(size, numSegments):
	for i in range(numSegments):
		lo = int(size * float(i)/numSegments)
		hi = int(size * float(i+1)/numSegments)
		yield (lo,hi)


def splitList(lst, numSegments):
    for (lo, hi) in splitRange(len(lst), numSegments):
        yield lst[lo:hi]


# A simple class which emulates the behavior of a Process Pool, but only uses
# one CPU.  Useful for 
class DefaultPool():
    def __init__(self):
        self._processes=1
    def map(self, fun, args):
        return map(fun, args)
        

def plot_speed(road_map, dt, filename):
    db_travel_times.load_travel_times(road_map, dt)
    title = str(dt)    
    
    road_map.save_speeds(filename + ".csv", num_trips_threshold=1)
    cmd = "Rscript analysis/plot_speeds.R '%s.csv' '%s' '%s'" % (filename, filename, title)
    print(cmd)
    system(cmd)
    remove(filename + ".csv")

def plot_group_of_speeds(road_map, dts, tmp_dir):
    road_map.unflatten()
    for dt in dts:
        out_file = path.join(tmp_dir, str(dts) + ".png")
        plot_speed(road_map, dt, out_file)


def plot_speeds_in_parallel(road_map, dts, tmp_dir="tmp", pool=DefaultPool()):
    pass


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