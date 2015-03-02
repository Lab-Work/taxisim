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


def splitLists(lst1, lst2, numSegments):
    for (lo, hi) in splitRange(len(lst1), numSegments):
        if(lst2==None):
            yield (lst1[lo:hi], None)
        else:
            yield (lst1[lo:hi], lst2[lo:hi])


# A simple class which emulates the behavior of a Process Pool, but only uses
# one CPU.  Useful for 
class DefaultPool():
    def __init__(self):
        self._processes=1
    def map(self, fun, args):
        return map(fun, args)
        

def plot_speed(road_map, dt, filename, speed_dict=None):
    
    #If no speed dict is given, load the speeds from the database
    if(speed_dict==None):
        db_travel_times.load_travel_times(road_map, dt)


    title = str(dt)    
    
    #print ("Saving to %s.csv" % filename)
    #road_map.save_speeds(filename + ".csv", num_trips_threshold=1)
    #cmd = "Rscript analysis/plot_speeds.R '%s.csv' '%s' '%s' > /dev/null" % (filename, filename, title)
    #print(cmd)
    #system(cmd)
    
    print("Processing %s" % title)
    
    if(speed_dict==None):
        plot_type="absolute"
    else:
        plot_type="zscore"
    
    
    p1 = Popen(['Rscript', 'traffic_estimation/plot_speeds_piped.R', filename, title, plot_type], stdout=PIPE, stdin=PIPE)
    
    
    # Get the speed data from the map in tabular form
    lines = road_map.get_speed_table(num_trips_threshold=0, speed_dict=speed_dict)
    # Convert table to CSV format and pipe it to the Rscript
    csv_lines = [",".join(map(str, line)) for line in lines]
    data = "\n".join(csv_lines)   
        
    
    
    cmds = ['Rscript', 'traffic_estimation/plot_speeds_piped.R', filename, title, plot_type]
    #print(" ".join(cmds))
    #print(data[:2000])
    #print ("  ==================   ")
    p1 = Popen(['Rscript', 'traffic_estimation/plot_speeds_piped.R', filename, title, plot_type], stdout=PIPE, stdin=PIPE)
    _ = p1.communicate(data) # R output is discarded
    #print(_)

    #remove(filename + ".csv")

def plot_group_of_speeds((dts, speed_dicts), road_map, tmp_dir):
    road_map.unflatten()
    db_main.connect("db_functions/database.conf")
    for i in range(len(dts)):
        dt = dts[i]
        if(speed_dicts==None):
            speed_dict = None
        else:
            speed_dict = speed_dicts[i]
        
        out_file = path.join(tmp_dir, str(dt) + ".png")
        plot_speed(road_map, dt, out_file, speed_dict=speed_dict)
    db_main.close()


def plot_speeds_in_parallel(road_map, dts, speed_dicts=None, tmp_dir="analysis/tmp", pool=DefaultPool()):
    road_map.flatten()
    plt_speeds_fun = partial(plot_group_of_speeds, road_map=road_map, tmp_dir = tmp_dir)
    
    list_it = splitLists(dts, speed_dicts, pool._processes)
    pool.map(plt_speeds_fun, list_it)



def build_speed_dicts(consistent_link_set, zscore_vectors):
    speed_dicts = []
    
    for vect in zscore_vectors:
        speed_dict = {}
        for i in range(len(vect)):
            speed_dict[consistent_link_set[i]] = vect[i,0]
        speed_dicts.append(speed_dict)
    
    return speed_dicts
            


def make_video(tmp_folder, filename_base, pool=DefaultPool(), dates=None, speed_dicts=None):
    rmtree(tmp_folder, ignore_errors=True)
    mkdir(tmp_folder)
    #pool = DefaultPool()
    print("Loading map")
    road_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    
    if(dates==None):
        dates = [datetime(2012,10,21) + timedelta(hours=1)*x for x in range(168*3)]
    print ("We have %d dates" % len(dates))
    plot_speeds_in_parallel(road_map, dates, speed_dicts=speed_dicts, tmp_dir=tmp_folder, pool=pool)
    
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