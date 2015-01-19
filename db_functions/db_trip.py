# -*- coding: utf-8 -*-
"""
Contains the Trip class, which represents a single taxi trip.

This Trip class is an updated version of the old one which takes trip info from csv files. Instead, it receives trip info from database cursor. Its attributes are also expanded to include fare-related records.

Created on Tuesday Jan 13 12:56:56 2015

@author: Fangyu Wu (fangyuwu@outlook.com)
"""

import db_main
from Trip import Trip


#Fetch trips from database with pickup_datetime between two datetimes
def find_pickup_dt(dt1, dt2):
	SQL = """SELECT * FROM trip
	WHERE %s <= pickup_datetime 
	AND pickup_datetime <= %s
	ORDER BY pickup_datetime, dropoff_datetime"""
	cur = db_main.execute(SQL, (str(dt1), str(dt2)))
	return [Trip(record) for record in cur]
	
#Fetch trips from database with dropoff_datetime between two datetimes
def find_dropoff_dt(dt1, dt2):
	SQL = """SELECT * FROM trip
	WHERE %s <= dropoff_datetime 
	AND dropoff_datetime <= %s
	ORDER BY pickup_datetime, dropoff_datetime"""
	cur = db_main.execute(SQL, (str(dt1), str(dt2)))
	return [Trip(record) for record in cur]

#Fetch trips from database with day_of_week and hours_of_day of interest
def find_dow_hod(dow, hod):
	SQL = """SELECT * FROM trip
	WHERE day_of_week = %s
	AND hours_of_day = %s
	ORDER BY pickup_datetime, dropoff_datetime"""
	cur = db_main.execute(SQL, (dow, hod))
	return [Trip(record) for record in cur]
			



