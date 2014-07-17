import Queue
import datetime
import csv
import timeit
import sys
import random
from math import sqrt

from node import node, getNodes, getNodeRange
from aStar import aStar
from windingFactor import estimateActual, estimateTime
"""
medallion, hack_liticense, vendor_id, rate_code, store_and_fwd_flag, pickup_datetime, dropoff_datetime, passenger_count, trip_time_in_secs, trip_distance, pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude, payment_type, fare_amount, surcharge, mta_tax, tip_amount, tolls_amount, total_amount
C98556CF31B2CE2C9C85A1FC57B8117C,02C57D2D0045A3B46D9D48B333F9970F,VTS,1,,2013-01-01 00:00:00,2013-01-01 00:28:00,1,1680,3.94,-73.990784,40.76088,-73.954185,40.778847,CSH,20.5,0.5,0.5,0,0,21.5
"""
#########################################
#########################################
#										#
#				Functions				#
#										#
#########################################
#########################################

#Standard Euclidean distance calculator for latitude and longitude, which we also convert to miles (based off factors we found converting spherical to cartesian coordinates)
def distance(lat1, long1, lat2, long2):
	diffLat = float(lat1) - float(lat2)
	diffLong = float(long1) - float(long2)
	latMiles = diffLat * 111194.86461 #meters per degree latitude, an approximation  based off our latitude and longitude
	longMiles = diffLong * 84253.1418965 #meters per degree longitude, an approximation  based off our latitude and longitude
	return sqrt(latMiles * latMiles + longMiles * longMiles)

#Based off its format in the CSV file creates an actual datetime object
def createdatetime(DateTime):
	return datetime.datetime(year = int(DateTime[0:4]), month = int(DateTime[5:7]), day = int(DateTime[8:10]), hour = int(DateTime[11:13]), minute = int(DateTime[14:16]), second = int(DateTime[18:]))

#Given a difference in seconds, creates a new datetime object that far into the future
def changeTime(dateTime, secondsPassed):
	delta = datetime.timedelta(seconds = secondsPassed)
	return dateTime + delta

#####################################
#####################################
#									#
#				Taxi				#
#									#
#####################################
#####################################

class taxi:

	#This is a taxi object, which keeps track of a unique ID number, the time at which it goes off the clock, and a latitude and longitude 		which initially are generated at some random point between the lowest and highest possible longitude and latitude
	def __init__(self, NODEINFO, ID, KILLTIME):
		self.id = ID
		self.killTime = KILLTIME
		#NODEINFO = [MaxLat, MinLat, MaxLong, MinLong]
		self.lat = (NODEINFO[0] - NODEINFO[1]) * random.random() + NODEINFO[1]
		self.long = (NODEINFO[2] - NODEINFO[3]) * random.random() + NODEINFO[3]

	#At the end of each dropoff, we check to see if it is time for this taxi to go off the clock. This function takes the time the dropoff 		occurs and sees if it is past the killTime
	def isTimeToKill(self, currTime):
		#For now, always return false
		return False
		if currTime >= self.killTime:
			return True
		return False

	#Checks if a taxi has this medallion
	def isTaxi(self, medallion):
		if self.id == medallion:
			return True
		return False

#########################################
#########################################
#										#
#				Simulation				#
#										#
#########################################
#########################################

class simulation:
	
	def __init__(self):
		#In order to quickly facilitate looking through the map, we have broken it up into an NxN grid. self.gridSize = N.
		self.gridSize = 18

		#The grid object, which contain gridRegions that contain nodes that represent intersections.
		self.grid = getNodes(self.gridSize)

		#The maximum and minimum latitude and longitude represented in the nodes
		self.nodeInfo = getNodeRange()

		#A queue of events, which include Pickup, Dropoff, PickupRequest, and WakeUp
		self.simulationQueue = Queue.PriorityQueue()
	
		#Taxis that are currently with customers and active
		self.taxisInUse = set()

		#Taxis that are active but not currently with customers. These are presumed to be waiting on the side of the street.
		self.taxisAvailable = set()
	
		#Customers that are waiting for a taxi to become available
		self.customersWaiting = []

		#Keeps track of total distance travelled on HIDDEN TRIPS ONLY
		self.distanceTravelled = 0

		#Keeps track of how many times a customer requested a taxi but none were available
		self.taxiNeeded = 0

		#Keeps track of which month and year we are in
		self.fileNum = 0

		self.finishedWithFiles = False

		#Keeps track of the latest time in the file
		self.latestFileTime = createdatetime("2009-12-31 23:56:30")

		#Keeps track of the latest time in the simulation
		self.latestSimulationTime = createdatetime("2010-01-01 00:00:00")


	#################################
	#								#
	#		Running Simulation		#
	#								#
	#################################

	def tempGetTaxis(self):
		for i in range(100):
			self.taxisAvailable.add(taxi(self.nodeInfo, i, "00:00:00"))
	#Because it take O(log(N)) time to look through the priorityqueue, our goal is to keep it fairly empty. In this way, we add a certain 		amount of pickup requests at a time, any time the queue becomes less than 100 long.
	def putIntoQueue(self):
		global FILES
		print "Putting more into queue"
		for i in range(tripsToReadAtATime):
			try:
				nextRow = FILES[self.fileNum].next()
				rowList = nextRow.split(',')
				if rowList[0] == "medallion":
					continue
				#Because we don't want to run an event (like a dropoff) before we generate the pickups earlier than it, we must keep track 					of the times in the file and load them accordingly
				if i == tripsToReadAtATime - 1:
					self.latestFileTime = createdatetime(nextRow.split(',')[5])
				self.generatePickupRequest(nextRow.split(','))
			#If we get this exception, we have finished with the file and must move on with the next one
			except(StopIteration):
				self.fileNum += 1
				if fileNum == len(FILES):
					self.finishedWithFiles = True
					return
				i -= 1

	def runSimulation(self):
		#Start by putting some pickups in the queue
		self.putIntoQueue()
		self.tempGetTaxis()
		while not self.simulationQueue.empty():
			#If at any point the event we created is happens later than the pickups we generated, we need to be sure no pickups happened 				between our last pickup and the dropoff, so that is our indicator to fill the queue more
			while not self.finishedWithFiles and self.latestSimulationTime > self.latestFileTime:
				self.putIntoQueue()

			#An event is formatted like this -> (TimeEventShouldOccur, EventName, TaxiAssociatedWithEvent, ArrayAssociatedWithEvent)
			currEvent = self.simulationQueue.get()
			if currEvent[0] > createdatetime("2010-01-02 00:00:00"):
				break

			print currEvent
			#The method to call is synonymous with the event name
			methodToCall = getattr(self, currEvent[1])
			methodToCall(currEvent[2], currEvent[3], currEvent[0])

	#################################
	#								#
	#		All Event Creating		#
	#								#
	#################################
	#NOTE: At the creation of every event, we check the time the event will occur, and update the latestSimulationTime accordingly.

	#Creates the pickup event (the time is generated during the PickupRequest)
	def generatePickup(self, taxi, arrayFromCSV, eventTime):
		if eventTime > self.latestSimulationTime:
			self.latestSimulationTime = eventTime
		self.simulationQueue.put((eventTime, "Pickup", taxi, arrayFromCSV))

	#The pickup request is generated during the addToQueue function, and adds a pickupRequest onto the evet list. A customer is estimated 		to be ready	4.5 minutes before their actual real world pickup 
	def generatePickupRequest(self, arrayFromCSV):
		eventTime = createdatetime(arrayFromCSV[5])
		newEventTime = changeTime(eventTime, -270)
		if newEventTime > self.latestSimulationTime:
			self.latestSimulationTime = newEventTime
		self.simulationQueue.put((newEventTime, "PickupRequest", None, arrayFromCSV))

	#Calculates the time of trip and adds it onto the pickupTime to get the dropoff time
	def generateDropoff(self, taxi, arrayFromCSV, pickUpTime):
		#Gets us the trip time in seconds
		timeDelta = createdatetime(arrayFromCSV[6]) - createdatetime(arrayFromCSV[5])
		newEventTime = pickUpTime + timeDelta
		if newEventTime > self.latestSimulationTime:
			self.latestSimulationTime = newEventTime
		self.simulationQueue.put((newEventTime, "Dropoff", taxi, arrayFromCSV))

	#Activates a taxi - puts it onduty from offduty
	def generateWakeup(self, taxiID, arrayFromCSV, eventTime, killTime):
		newTaxi = taxi(taxiID, killTime)
		self.simulationQueue.put(eventTime, "Wakeup", newTaxi, None)

	#################################
	#								#
	#		All Event Handling		#
	#								#
	#################################

	#TODO: REMOVE THIS EVENT, WE DON'T NEED IT
	#The moment a customer is picked up, they should be ready to be dropped off
	def Pickup(self, taxi, arrayFromCSV, timeOccurred):
		self.generateDropoff(taxi, arrayFromCSV, timeOccurred)
	
	#Finds the taxi closest to a customer and then assigns that taxi to pickup the customer
	def PickupRequest(self, TAXINOTNEEDED, arrayFromCSV, timeRequested):
		global searchAlgorithm, searchRadius
		#Occasionally a customer's data is bad, and we opt to throw those events out
		if  float(arrayFromCSV[10]) == 0 or float(arrayFromCSV[11]) == 0 or float(arrayFromCSV[12]) == 0 or float(arrayFromCSV[13]) == 0:
			print "BAD CUSTOMER LONG/LAT"
			return

		#If there are no taxis available, we assign the customers to the waiting array so when a taxi is freed up we can pick them up
		if len(self.taxisAvailable) == 0:
			self.customersWaiting.append((timeRequested, arrayFromCSV))
			self.taxiNeeded += 1
			return

		custLong = float(arrayFromCSV[10])
		custLat = float(arrayFromCSV[11])
		taxiList = []
		#We sort the taxis by their distance by making tuples (distance, taxi)
		for taxi in self.taxisAvailable:
			taxiList.append((distance(taxi.lat, taxi.long, custLat, custLong), taxi))
		taxiList.sort(key = lambda taxi: taxi[0])
		#Using either the A* algorithm ('A') or the winding factor ('W') finds the closest taxi.
		bestTaxi = None
		bestDistance = 10000000
		if searchAlgorithm == 'A':
			for taxi in taxiList:
				#We sorted them all by Euclidean distance - if the current best distance is smaller than the current euclidean distance 				(the shortest distance) then we don't need to check anymore as none can be closer
				if taxi[0] > bestDistance or taxi[0] > searchRadius:
					break
				currDistance = aStar(taxi[1].long, taxi[1].lat, custLong, custLat, self.grid, self.nodeInfo, self.gridSize)
				if currDistance < bestDistance:
					bestTaxi = taxi[1]
					bestDistance = currDistance

		if searchAlgorithm == 'W':
			for taxi in taxiList:
				#We sorted them all by Euclidean distance - if the current best distance is smaller than the current euclidean distance 				(the shortest distance) then we don't need to check anymore as none can be closer
				if taxi[0] > bestDistance or taxi[0] > searchRadius:
					break
				currDistance = estimateActual(taxi[1].lat, taxi[1].long, custLat, custLong)
				if currDistance < bestDistance:
					bestTaxi = taxi[1]
					bestDistance = currDistance

		#If all were outside the search radius, then no taxis will have picked them up and thus no customers would have been found
		if bestTaxi == None:
			self.customersWaiting.append((timeRequested, arrayFromCSV))
			self.taxiNeeded += 1
			return
		
		
		#This is what we are hoping to minimize, so we keep track of it all
		self.distanceTravelled += bestDistance

		#For now, convert to time by assuming they are going twenty miles per hour
		bestTime = (bestDistance / float(5280)) / 20  * 3600 #20 mph and 3600 seconds per hour
	
		#We must remove the taxi from available taxis but add them to the ones in use
		self.taxisInUse.add(bestTaxi)
		self.taxisAvailable.discard(bestTaxi)
		self.generatePickup(bestTaxi, arrayFromCSV, changeTime(timeRequested, bestTime))

	#TODO: Check if customers are waiting in queue
	#Drops off the customer and decides if it is time to relieve the taxi from duty. It also will check if customers are waiting and get to them if necessary
	def Dropoff(self, taxi, arrayFromCSV, currTime):
		if taxi.isTimeToKill(currTime):
			self.taxisInUse.discard(taxi)

#		elif len(self.customersWaiting) == 0:
#			taxi.lat = float(arrayFromCSV[13])
#			taxi.long = float(arrayFromCSV[12])
#			self.taxisInUse.discard(taxi)
#			self.taxisAvailable.add(taxi)
		taxi.lat = float(arrayFromCSV[13])
		taxi.long = float(arrayFromCSV[12])
		self.taxisInUse.discard(taxi)
		self.taxisAvailable.add(taxi)

#10 long, 11 lat
#Sort by distance, not waiting
		else:
			print "Alec will TOTALLY implement this later"

	#When activated, a taxi will be added to the available taxis
	def Wakeup(self, taxi, ARRAYNOTNEEDED, TIMENOTNEEDED):
		self.taxisAvailable.add(taxi)

if __name__ == "__main__":

	if len(sys.argv) < 3:
		print "Please give two arguments to this - search algorithm (A or W) and search radius (number)"
		sys.exit()
	searchAlgorithm = sys.argv[1]
	searchRadius = sys.argv[2]

	#Make 
	FILENAMES = []
	for j in range(3):
		for i in range(1, 10):
			FILENAMES.append("../../Desktop/LAB_SERVER/taxi_data/data_chron/FOIL201" + str(j) + "/trip_0" + str(i) + ".csv")
		for i in range(10, 13):
			FILENAMES.append("../../Desktop/LAB_SERVER/taxi_data/data_chron/FOIL201" + str(j) + "/trip_" + str(i) + ".csv")


	FILES = []
	for name in FILENAMES:
		FILES.append(open(name, 'r'))

	tripsToReadAtATime = 100
	theSimulation = simulation()
	theSimulation.runSimulation()



"""
	def getAllTaxis(self):
		global FILENAMES
		for FILENAME in FILENAMES:
			allTrips = open(FILENAME, 'r')
			allTaxis = set()
			i = 0
			for row in allTrips:
			#	if i % 100000 == 0:
			#		print str(i) + "/10000000 done!"
				if i > TRIPSTOREADATATIME:
					break
			#	self.taxisOff.add(taxi(taxiID, KILLTIMENEEDED))
			#For now, all taxis are available
				self.taxisAvailable.add(taxi(row[0], 0))
				i += 1
"""
