import csv
import os
import shutil
from datetime import *
from multiprocessing import Process
from time import sleep
import shutil

from MITSpeedAlgorithm import MITSpeedAlgorithm

#2011-05-08

start_time = datetime.now()

class ParseFileProcess(Process):
	def __init__(self, direc, dateTime):
		super(ParseFileProcess, self).__init__()
		self.fileToRead = "../data_chron/FOIL2011/trip_05.csv"
		#Directory + weekday (0 = Sunday, 6 = Saturday) + hour (0-23)
		self.path = direc
		self.startTime = dateTime
		print dateTime
		self.endTime = dateTime + timedelta(hours = 1) - timedelta(microseconds = 1)
		filename = tmp_dir + "/" + str((dateTime.weekday() + 1) % 7) + "_" + str(dateTime.hour)
		print filename
		self.fileToWrite = filename
		
	#Run when start is called
	def run(self):
		print "Running"
		MITSpeedAlgorithm(self.fileToRead, self.startTime, self.endTime, self.fileToWrite)


tmp_dir = "speeds_per_hour"
#shutil.rmtree(tmp_dir, ignore_errors=True)
#os.mkdir(tmp_dir)


NUM_PC = 7

workers = [None] * NUM_PC

#When we know howto end the simulation
killTime = datetime(year = 2011, month = 5, day = 15) 
latestTime = datetime(year = 2011, month = 5, day = 8)

latestTime = latestTime + timedelta(days = 3, hours = 14)

latestTime = latestTime - timedelta(hours = 1)
while latestTime < killTime:
			
	created_job = False
	#Polling - see if any workers are ready to accept a new job
	while(not created_job):
		for i in range(NUM_PC):
			if(workers[i]==None or not workers[i].is_alive()):
				if workers[i] != None:
					workers[i].join()
				latestTime = latestTime + timedelta(hours = 1)
				workers[i] = ParseFileProcess(tmp_dir, latestTime)

				#Causes the run file to begin
				workers[i].start()
				created_job = True
				break
				
		#Sleep for 1 second so the polling doesn't hog a CPU
		if(not created_job):
			sleep(1)
for w in workers:
	if(w!=None and w.is_alive()):
		w.join()


