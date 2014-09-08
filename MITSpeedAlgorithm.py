import csv
import timeit
from datetime import *
from node import getCorrectNodes, getNodeRange
from aStar import aStar
from trip import trip
from math import sqrt

#####################################
#									#	
#			  FUNCTIONS				#
#									#
#####################################

#Standard Euclidean distance multiplied given our region of space (NYC), where I converted it to a plane using Spherical -> cartesian coordinates.
def distance(lat1, long1, lat2, long2):
	diffLat = float(lat1) - float(lat2)
	diffLong = float(long1) - float(long2)
	latMiles = diffLat * 111194.86461 #meters per degree latitude, an approximation  based off our latitude and longitude
	longMiles = diffLong * 84253.1418965 #meters per degree longitude, an approximation  based off our latitude and longitude
	return sqrt(latMiles * latMiles + longMiles * longMiles)

def outOfBounds(LONG, LAT, NODEINFO):
	if LAT >= NODEINFO[0] or LAT < NODEINFO[1] or LONG >= NODEINFO[2] or LONG < NODEINFO[3]:
		return True
	return False

#Given a longitude and latitude, figures out which node is closest to it
def findNodes(LONG, LAT, gridOfNodes, NODEINFO, N):
	if outOfBounds(LONG, LAT, NODEINFO):
	#	print "OUT OF BOUNDS: (Long, Lat) = (" + str(LONG) + ", " + str(LAT) + ")"
		return None	
	#Node closest to coords and its distance
	bestNode = None
	bestDistance = 1000000
	i = int(float(LONG - NODEINFO[3]) * N/ float(NODEINFO[2] - NODEINFO[3]))
	j = int(float(LAT - NODEINFO[1]) * N/ float(NODEINFO[0] - NODEINFO[1]))

	#You have to check the surrounding area (if a coordinate is really close to the edge of the region[i][j] it could be in a different 	region [i - 1][j] for example
	if i != 0:
		i -= 1
	if j != 0:
		j -= 1
	for n in range(3):
		if i + n >= len(gridOfNodes):
			break
		for m in range(3):
			if j + m >= len(gridOfNodes[0]):
				break
			gridRegion = gridOfNodes[i + n][j + m]
			for node in gridRegion.nodes:
				currDistance = distance(LAT, LONG, node.lat, node.long)
				if currDistance < bestDistance:
					bestNode = node
					bestDistance = currDistance
	return bestNode

#Based off its format in the CSV file creates an actual datetime object
def createdatetime(DateTime):
	return datetime(year = int(DateTime[0:4]), month = int(DateTime[5:7]), day = int(DateTime[8:10]), hour = int(DateTime[11:13]), minute = int(DateTime[14:16]), second = int(DateTime[18:]))

#This algorithm takes a street and returns the set of all streets that intersect the original street and have been granted a velocity
def findAdjacent(nodeTuple, dictOfStreets):
	allAdjacent = set()
	for node in nodeTuple[0].distanceConnections:
		if (nodeTuple[0].id, node.id) in dictOfStreets:
			allAdjacent.add((nodeTuple[0], node))
	for node in nodeTuple[0].backwardsConnections:
		if (node.id, nodeTuple[0].id) in dictOfStreets:
			allAdjacent.add((node, nodeTuple[0]))
	for node in nodeTuple[1].distanceConnections:
		if (nodeTuple[1].id, node.id) in dictOfStreets:
			allAdjacent.add((nodeTuple[1], node))
	for node in nodeTuple[1].backwardsConnections:
		if (node.id, nodeTuple[1].id) in dictOfStreets:
			allAdjacent.add((node, nodeTuple[1]))
	return allAdjacent

def getAllStreets(gridOfNodes):
	allStreets = set()
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
				for connection in node.distanceConnections:
					allStreets.add((node, connection))
	return allStreets

def removeLoopTrips(trips):
	newTrips = []
	for trip in trips:
		if trip.startNode != trip.endNode:
			newTrips.append(trip)
	return newTrips

def removeExtremeTrips(trips):
	newTrips = []
	for trip in trips:
		if float(trip.tripTime) >= 120 and float(trip.tripTime) <= 3600:
			newTrips.append(trip)
	return newTrips 

def removeSpeedTrips(trips):
	newTrips = []
	for trip in trips:
		try:
			if float(findLength(trip.nodeList))/float(trip.tripTime) >= .5 and float(findLength(trip.nodeList))/float(trip.tripTime) <= 30:
				newTrips.append(trip)
		except(IndexError):
			i = 1
	return newTrips

def buildDictionary(path):
	dictionary = dict()
	for i in range(len(path) - 1):
		currNode = path[i]
		nextNode = path[i + 1]
		ID = (currNode.id, nextNode.id)
		dictionary[ID] = (currNode, nextNode)
	return dictionary

def findTime(arr):
	if arr == "No Path Found":
		print "COULDN'T FIND PATH"
		return 10000000
	totalTime = 0
	for i in range(len(arr) - 1):
		currNode = arr[i]
		nextNode = arr[i + 1]
		totalTime += float(currNode.timeConnections[nextNode])
	return totalTime

def findLength(arr):
	if arr == "No Path Found":
		print "COULDN'T FIND PATH"
		return 10000000
	totalLength = 0
	for i in range(len(arr) - 1):
		currNode = arr[i]
		nextNode = arr[i + 1]
		totalLength += float(currNode.distanceConnections[nextNode])
	return totalLength

def buildAllStreetsUsed(path):
	if arr == "No Path Found":
		print "COULDN'T FIND PATH"
		return 10000000
	newSet = set()
	for i in range(len(path) - 1):
		currNode = path[i]
		nextNode = path[i + 1]
		newSet.add((currNode.id, nextNode.id))
	return newSet

def getSortedUnusedStreets(allStreets, dictOfStreets):
	unusedStreets = []
	for street in allStreets:
		if (street[0].id, street[1].id) not in dictOfStreets:
			allAdjacent = findAdjacent(street, dictOfStreets)
			unusedStreets.append((len(allAdjacent), street))
	unusedStreets.sort(key = lambda street: street[0])
	unusedStreets = unusedStreets[::-1]
	return unusedStreets


def MITSpeedAlgorithm(readFrom, startTime, killTime, fileName):
	#####################################
	#									#	
	#			 	PART 1:				#
	#		  CONDENSE DUPLICATES		#
	#									#
	#####################################

	#We will be using a NxN grid, where each region has a set of nodes, to make it easier to seek out nodes
	fastestSpeed = 5 #meters per second
	initSpeed = 5 #meters per second
	N = 20
	#Gets all of the nodes
	gridOfNodes = getCorrectNodes(N, None, None)
	nodeInfo = getNodeRange()
	tripFile = csv.reader(open(readFrom, 'rb'))
	tAgg = []
	#Each keeps track of distinct trips, so we can filter out duplicates and replace them with a great average trip
	dictionaryCab = dict()
	dictionaryTimeAgg = dict()
	dictionaryCounter = dict()
	dictionaryDistance = dict()
	header = True
	for row in tripFile:
		if not header:
			if row[5] > str(killTime):
				print row[5]
				break
			if row[5] >= str(startTime):
				try:
					beginNode = findNodes(float(row[10]), float(row[11]), gridOfNodes, nodeInfo, N)
					endNode = findNodes(float(row[12]), float(row[13]), gridOfNodes, nodeInfo, N)
				except(ValueError):
					continue
				if beginNode == None or endNode == None:
					continue
				newEntry = (beginNode.id, endNode.id)
				dictionaryCab[newEntry] = row
				if newEntry in dictionaryTimeAgg:
					dictionaryTimeAgg[newEntry] += float((createdatetime(row[6]) - createdatetime(row[5])).seconds)
					dictionaryDistance[newEntry] += float(row[9])
					dictionaryCounter[newEntry] += 1
				else:
					dictionaryTimeAgg[newEntry] = float((createdatetime(row[6]) - createdatetime(row[5])).seconds)
					dictionaryDistance[newEntry] = float(row[9])
					dictionaryCounter[newEntry] = 1
		header = False

	#Replaces the single trip with a trip object and adds it to our set of all trips
	for key in dictionaryTimeAgg:
		#The current trip row
		t = dictionaryCab[key]
		newTime = dictionaryTimeAgg[key]/dictionaryCounter[key]
		newDistance = dictionaryDistance[key]/dictionaryCounter[key]
		#The new trip array that initializes a trip object
		newTripList = [t[0], newTime, newDistance,t[10],t[11],t[12],t[13],key[0],key[1], dictionaryCounter[key]]
		newTrip = trip(newTripList)
		tAgg.append(newTrip)

	print len(tAgg)

	#####################################
	#									#	
	#				PART 2:				#
	#		   REMOVE SHORT/LONG		#
	#									#
	#####################################

	#This removes any trip that starts and ends at the same node, as long as extremely short or extremely long trips
	tAgg = removeLoopTrips(tAgg)
	tAgg = removeExtremeTrips(tAgg)

	#####################################
	#									#	
	#				PART 3:				#
	#			COMPUTE TRIPS			#
	#									#
	#####################################


	for aTrip in tAgg:
		path = aStar(aTrip.startLong, aTrip.startLat, aTrip.endLong, aTrip.endLat, gridOfNodes, nodeInfo, N, fastestSpeed)
		aTrip.nodeList = path

	#####################################
	#									#	
	#				PART 4:				#
	#		   REMOVE FAST/SLOW			#
	#									#
	#####################################

	tAgg = removeSpeedTrips(tAgg)
	print len(tAgg)

	#############################################
	#############################################
	#											#	
	#					PART 5:					#
	#				ITERATIVE PART				#
	#											#
	#############################################
	#############################################


	#MIRROR OF PSUEDO CODE: PART 5.1, SET AGAIN = TRUE
	again = True

	#This is a dictionary of sets - give it a streetID (startnode.id, endnode.id) and it will return the set of trips that include 	that street and O_s
	dictOfStreets = dict()
	timeOuterLoop = 0
	timeInnerLoop = 0
	iterOuterLoop = 0
	iterInnerLoop = 0

		#####################################
		#									#	
		#			 -PART 5.2-				#
		#			 OUTER LOOP				#
		#									#
		#####################################
	while again:

		#Now the we are out of the Inner Loop, we must reset the times associated with each trip
		print "Outer Loop!"
		start = timeit.default_timer()
		for ID in dictOfStreets:
			tripsWithStreet = dictOfStreets[ID][0]
			randomTrip = next(iter(tripsWithStreet)) #All the streets have the street, so we can pick any one

			#nodeTuple[0] = startNode, nodeTuple[1] = endNode
			nodeTuple = randomTrip.nodeDict[ID]
			newTime = nodeTuple[0].distanceConnections[nodeTuple[1]] / nodeTuple[0].speedConnections[nodeTuple[1]]
			nodeTuple[0].timeConnections[nodeTuple[1]] = newTime
		print "End of resetting times"

		#We now have an entirely new set of streets used, so we must reset the old dictionary
		dictOfStreets = dict()

		again = False
		RelError = 0
		#We find new paths based off of the new times we got
		for aTrip in tAgg:
			path = aStar(aTrip.startLong, aTrip.startLat, aTrip.endLong, aTrip.endLat, gridOfNodes, nodeInfo, N, fastestSpeed)
			aTrip.nodeList = path
			aTrip.nodeDict = buildDictionary(path)
			for ID in aTrip.nodeDict:
				if ID in dictOfStreets:
					dictOfStreets[ID][0].add(aTrip)
				else:
					dictOfStreets[ID] = (set(), 0)
					dictOfStreets[ID][0].add(aTrip)
			aTrip.estTime = findTime(path)
			RelError += abs(aTrip.estTime - aTrip.tripTime)/aTrip.tripTime
		print "End of getting RelError, finding paths, filling dictionaryand getting streetIDs"


		#Offset Computation
		for ID in dictOfStreets:
			offSet = 0
			for aTrip in dictOfStreets[ID][0]:
				offSet += (aTrip.estTime - aTrip.tripTime) * aTrip.numTrips
			dictOfStreets[ID] = (dictOfStreets[ID][0], offSet)
		print "End of calculating offset coefficients"
		k = 1.2
		stop = timeit.default_timer()
		timeOuterLoop += (stop - start)
		iterOuterLoop += 1
		print stop - start

		#####################################
		#									#	
		#			 -PART 5.3-				#
		#			 INNER LOOP				#
		#									#
		#####################################
		print "Inner Loop!"
	#MIRROR OF PSUEDO CODE: PART 5.3, INNER LOOP (KEEP TRACK OF FASTEST SPEED HERE)
		while True:
		
			start = timeit.default_timer()
			#Recalculates the time with a different ratio 
			for ID in dictOfStreets:
				tripsWithStreet = dictOfStreets[ID][0]
				randomTrip = next(iter(tripsWithStreet)) #It doesn't matter what trip we take from this set, as they all include this street
				nodeTuple = randomTrip.nodeDict[ID]
				if dictOfStreets[ID][1] < 0:
					nodeTuple[0].timeConnections[nodeTuple[1]] = nodeTuple[0].timeConnections[nodeTuple[1]] * k
				else: 
					nodeTuple[0].timeConnections[nodeTuple[1]] = nodeTuple[0].timeConnections[nodeTuple[1]] / k
			#Figures out what the error would be under these new time constraints
			NewRelError = 0
			for aTrip in tAgg:
				etPrime = findTime(aTrip.nodeList)
				NewRelError += abs(etPrime - aTrip.tripTime)/aTrip.tripTime
			#Our new times are more accurate - time to redo everything
			if NewRelError < RelError:
				#We are going to have a new fastest speed
				fastestSpeed = -1
				RelError = NewRelError
				#Since our new times are better, we ReUpdate the speed based off these new times
				for ID in dictOfStreets:
					tripsWithStreet = dictOfStreets[ID][0]
					randomTrip = next(iter(tripsWithStreet)) #It doesn't matter what trip we take from this set, as they all include this street
					nodeTuple = randomTrip.nodeDict[ID]
					newSpeed = nodeTuple[0].distanceConnections[nodeTuple[1]] / nodeTuple[0].timeConnections[nodeTuple[1]]
					if newSpeed > fastestSpeed:
						fastestSpeed = newSpeed
					nodeTuple[0].speedConnections[nodeTuple[1]] = newSpeed
				again = True
			else:
				#Continue reducing k
				iterInnerLoop += 1
				k = 1 + (k - 1) * .75
				if k < 1.0001:
					stop = timeit.default_timer()
					timeInnerLoop += (stop - start)
					print stop - start
					break

	#TODO: TEST TO MAKE SURE TIMES ARE UP-TO-DATE
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
				for connection in node.timeConnections:
					node.timeConnections[connection] = node.distanceConnections[connection] / node.speedConnections[connection]

	#####################################
	#									#	
	#				PART 6:				#
	#		    UNUSED STREETS			#
	#									#
	#####################################

	print "Outer loop time:"
	print timeOuterLoop
	print "Inner loop time:"
	print timeInnerLoop
	print "Iterations outer:"
	print iterOuterLoop
	print "Iterations inner:"
	print iterInnerLoop

	#A set of pairs of nodes (startNode, endNode)
	allStreets = getAllStreets(gridOfNodes)
	unusedStreets = getSortedUnusedStreets(allStreets, dictOfStreets)
	prevLen = -1
	#We now set every street in order, averaging the velocity along each street and the times, then assigning it to the usedStreet set
	while True:
		if prevLen == len(unusedStreets):
			print prevLen
			for street in unusedStreets:
				currPair = street[1]
				currPair[0].speedConnections[currPair[1]] = -1
				currPair[0].timeConnections[currPair[1]] = -1
			break
		prevLen = len(unusedStreets)
		for street in unusedStreets:
			if street[0] == 0:
				unusedStreets = getSortedUnusedStreets(allStreets, dictOfStreets)
				break
			currPair = street[1]
			allAdjacent = findAdjacent(currPair, dictOfStreets)
			allVelocities = 0
			for nodeTuple in allAdjacent:
				allVelocities += nodeTuple[0].speedConnections[nodeTuple[1]]
			if len(allAdjacent) != 0:
				allVelocities /= len(allAdjacent)
			else:
				allVelocities = -1
			currPair[0].speedConnections[currPair[1]] = allVelocities
			if allVelocities != 0:
				currPair[0].timeConnections[currPair[1]] = currPair[0].distanceConnections[currPair[1]] / allVelocities
			else:
				currPair[0].timeConnections[currPair[1]] = -1
			dictOfStreets[(currPair[0].id, currPair[1].id)] = (currPair[0], currPair[1])

	#####################################
	#									#	
	#			 	PART 7:				#
	#		    WRITE LINK FILE	    	#
	#									#
	#####################################

	#Writes all of the pertinent information to a file, so that we can compare it to the link file later and add the time/speed
	linkFile = csv.writer(open(fileName, 'wb'))
	headers = ["begin_node_id","end_node_id","length","speed","time"]
	linkFile.writerow(headers)
	for nodeTuple in allStreets:
		newArr = [nodeTuple[0].id, nodeTuple[1].id, nodeTuple[0].distanceConnections[nodeTuple[1]], nodeTuple[0].speedConnections[nodeTuple[1]], nodeTuple[0].timeConnections[nodeTuple[1]]]
		linkFile.writerow(newArr)

