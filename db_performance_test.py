from db_functions import db_main, db_trip
import time
from threading import Timer
from datetime import datetime
import os
TIME = 3600
REPEAT = 24

def test():
	program_start = datetime.now()
	print "test started at: %s" %program_start.strftime("%Y-%m-%d %H:%M:%S")
	# Connect to the database
	db_main.connect("db_functions/database.conf")
	trips = db_trip.find_pickup_dt('2010-01-01 00:34:00', '2010-01-01 12:34:00')
	run_time = datetime.now() - program_start
	print run_time
	print len(trips)

def system():
	program_start = datetime.now()
	print "system status at: %s" %program_start.strftime("%Y-%m-%d %H:%M:%S")
	print os.system("ps -eo %cpu,%mem,pid,user,comm| sort -r | head -15")

print "performance test started at: %s" %datetime.now().strftime("%Y-%m-%d %H:%M:%S")
for t in range(REPEAT):
	Timer(t*TIME, test).start()
	Timer(t*TIME+10, system).start()

#one hour worths of trip
#duration
#number of trips
#ram&cpu
