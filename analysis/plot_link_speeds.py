# -*- coding: utf-8 -*-
"""
Created on Wed Jan 28 10:49:39 2015

@author: brian
"""
from datetime import datetime
from os import system, remove

from db_functions import db_main, db_travel_times
from routing import Map


def plot_speed(road_map, dt, filename):
    db_travel_times.load_travel_times(road_map, dt)
    
    road_map.save_speeds(filename + ".csv")
    system("Rscript analysis/plotmap %s %s.csv", (filename, filename))
    remove(filename + ".csv")
    


def plot_many_speeds():
    db_main.connect("db_functions/database.conf")
    dates = list(db_main.execute("SELECT DISTINCT datetime from travel_times"))
    print(str(dates))