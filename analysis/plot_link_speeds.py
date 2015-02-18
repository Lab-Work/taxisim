# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 10:49:39 2015

@author: brian
"""
from datetime import datetime, timedelta
from os import system, remove, path, mkdir
from shutil import rmtree
from multiprocessing import Pool
from subprocess import Popen, PIPE

from db_functions import db_main, db_travel_times
from routing.Map import Map
from functools import partial




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
    
    #print ("Saving to %s.csv" % filename)
    #road_map.save_speeds(filename + ".csv", num_trips_threshold=1)
    #cmd = "Rscript analysis/plot_speeds.R '%s.csv' '%s' '%s' > /dev/null" % (filename, filename, title)
    #print(cmd)
    #system(cmd)
    
    print("Processing %s" % title)
    p1 = Popen(['Rscript', 'analysis/plot_speeds_piped.R', filename, title], stdout=PIPE, stdin=PIPE)
    
    lines = [",".join(map(str, line)) for line in road_map.get_speed_csv(num_trips_threshold=0)]
    data = "\n".join(lines)    
    
    _ = p1.communicate(data)


    #remove(filename + ".csv")

def plot_group_of_speeds(dts, road_map, tmp_dir):
    road_map.unflatten()
    db_main.connect("db_functions/database.conf")
    for dt in dts:
        out_file = path.join(tmp_dir, str(dt) + ".png")
        plot_speed(road_map, dt, out_file)
    db_main.close()


def plot_speeds_in_parallel(road_map, dts, tmp_dir="analysis/tmp", pool=DefaultPool()):
    road_map.flatten()
    plt_speeds_fun = partial(plot_group_of_speeds, road_map=road_map, tmp_dir = tmp_dir)
    
    list_it = splitList(dts, pool._processes)
    pool.map(plt_speeds_fun, list_it)


def make_video(tmp_folder, filename_base):
    rmtree(tmp_folder, ignore_errors=True)
    mkdir(tmp_folder)
    pool = Pool(2)
    #pool = DefaultPool()
    print("Loading map")
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    dates = [datetime(2012,6,17) + timedelta(hours=1)*x for x in range(168)]
    print ("We have %d dates" % len(dates))
    plot_speeds_in_parallel(road_map, dates, tmp_dir=tmp_folder, pool=pool)
    
    print ("Combining frames into movie")
    #Combine all of the frames into a .avi movie
    cmd = 'mencoder "mf://%s/*.png" -mf fps=4 -o %s.avi -ovc lavc -lavcopts vcodec=msmpeg4v2:vbitrate=800' % (tmp_folder, filename_base)
    print(cmd)
    system(cmd)
    #convert the .avi movie into a couple other formats for convenience
    cmd = 'avconv -i %s.avi %s.mp4' % (filename_base, filename_base)
    print(cmd)
    system(cmd)
    cmd = 'avconv -i %s.avi %s.m4v' % (filename_base, filename_base)
    print(cmd)
    system(cmd)


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