import csv
import timeit
from node import getInitialNodes, getNodeRange
from aStar import aStar
from trip import trip

#TODO: Turn Street into class

#####################################
#									#	
#			  FUNCTIONS				#
#									#
#####################################

def findAdjacent(nodeTuple, dictOfStreets):
	allAdjacent = set()
	for node in nodeTuple[0].distanceConnections:
		if (nodeTuple[0].id, node.id) in dictOfStreets:
			allAdjacent.add(nodeTuple[0], node)
	for node in nodeTuple[0].backwardsConnections:
		if (node.id, nodeTuple[0].id) in dictOfStreets:
			allAdjacent.add(node, nodeTuple[0])
	for node in nodeTuple[1].distanceConnections:
		if (nodeTuple[1].id, node.id) in dictOfStreets:
			allAdjacent.add(nodeTuple[1], node)
	for node in nodeTuple[1].backwardsConnections:
		if (node.id, nodeTuple[1].id) in dictOfStreets:
			allAdjacent.add(node, nodeTuple[1])
	return numAdjacent

def getAllStreets(gridOfNodes):
	allStreets = set()
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
				for connection in node.distanceConnections:
					allStreets.add((node, connection))
	return allStreets

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

#####################################
#									#	
#			 	PART 1:				#
#		  CONDENSE DUPLICATES		#
#									#
#####################################

tripFile = csv.reader(open("someTrips.csv", 'rb'))
tAgg = []
#Each keeps track of distinct trips, so we can filter out duplicates and replace them with a great average trip
dictionaryCab = dict()
dictionaryTimeAgg = dict()
dictionaryCounter = dict()
dictionaryDistance = dict()
i = 0
for row in tripFile:
	if i != 0:
		newEntry = (row[7], row[8])
		dictionaryCab[newEntry] = row
		try:
			dictionaryTimeAgg[newEntry] += float(row[1])
			dictionaryDistance[newEntry] += float(row[2])
			dictionaryCounter[newEntry] += 1
		except(KeyError):
			dictionaryTimeAgg[newEntry] = float(row[1])
			dictionaryDistance[newEntry] = float(row[2])
			dictionaryCounter[newEntry] = 1
	i += 1

for key in dictionaryTimeAgg:
	t = dictionaryCab[key]
	newTime = dictionaryTimeAgg[key]/dictionaryCounter[key]
	newDistance = dictionaryDistance[key]/dictionaryCounter[key]
	t[1] = newTime
	t[2] = newDistance
	t.append(dictionaryCounter[key])
	newTrip = trip(t)
	tAgg.append(newTrip)

print len(tAgg)

#####################################
#									#	
#				PART 2:				#
#		   REMOVE SHORT/LONG		#
#									#
#####################################

#Note - I've removed all loop trips in the actual data, but for our actual running we need to filter them out. TODO
tAgg = removeExtremeTrips(tAgg)
print len(tAgg)

#####################################
#									#	
#				PART 3:				#
#			COMPUTE TRIPS			#
#									#
#####################################

#We will be using a NxN grid, where each region has a set of nodes, to make it easier to seek out nodes
N = 22 
fastestSpeed = 20 #meters per second
initSpeed = 20 #meters per second
gridOfNodes = getInitialNodes(N, initSpeed)
nodeInfo = getNodeRange()
start = timeit.default_timer()
i = 0
for trip in tAgg:
	if i > 1000:
		break
	path = aStar(trip.startLong, trip.startLat, trip.endLong, trip.endLat, gridOfNodes, nodeInfo, N, fastestSpeed)
	trip.nodeList = path
	i += 1
stop = timeit.default_timer()
print stop - start

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
	totalStreets = 0
	#We find new paths based off of the new times we got
	for trip in tAgg:
		path = aStar(trip.startLong, trip.startLat, trip.endLong, trip.endLat, gridOfNodes, nodeInfo, N, fastestSpeed)
		trip.nodeList = path
		trip.nodeDict = buildDictionary(path)
		totalStreets += len(trip.nodeDict)
		for ID in trip.nodeDict:
			try:
				dictOfStreets[ID][0].add(trip)
			except(KeyError):
				dictOfStreets[ID] = (set(), 0)
				dictOfStreets[ID][0].add(trip)
		trip.estTime = findTime(path)
		RelError += abs(trip.estTime - trip.tripTime)/trip.tripTime
	print "End of getting RelError, finding paths, filling dictionaryand getting streetIDs"


	#Offset Computation
	for ID in dictOfStreets:
		offSet = 0
		for trip in dictOfStreets[ID][0]:
			offSet += (trip.estTime - trip.tripTime) * trip.numTrips
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
		for trip in tAgg:
			etPrime = findTime(trip.nodeList)
			NewRelError += abs(etPrime - trip.tripTime)/trip.tripTime
		#Our new times are more accurate - time to redo everything
		if NewRelError < RelError:
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
			iterInnerLoop += 1
			k = 1 + (k - 1) * .75
			if k < 1.0001:
				stop = timeit.default_timer()
				timeInnerLoop += (stop - start)
				print stop - start
				break

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
unusedStreets = []
#According to the code, we need to sort the unused streets from most-to-least adjacent used
for street in allStreets:
	if (street[0].id, street[1].id) not in dictOfStreets:
		allAdjacent = findAdjacent(street, dictOfStreets)
		unusedStreets.append((len(allAdjacent), street))
unusedStreets.sort(key = lambda street: street[0], reversed = True)
#We now set every street in order, averaging the velocity along each street and the times, then assigning it to the usedStreet set
for street in unusedStreets:
	currPair = street[1]
	allAdjacent = findAdjacent(currPair, dictOfStreets)
	allVelocities = 0
	for nodeTuple in allAdjacent:
		allVelocities += nodeTuple[0].speedConnections[nodeTuple[1]]
	allVelocities /= len(allAdjacent)
	currPair[0].speedConnections[currPair[1]] = allVelocities
	currPair[0].timeConnections[currPair[1]] = currPair[0].distanceConnections[currPair[1]] / allVelocities
	dictOfStreets[(currPair[0].id, currPair[1].id)] = (currPair[0], currPair[1])


#####################################
#									#	
#			 	PART 7:				#
#		    WRITE LINK FILE	    	#
#									#
#####################################


linkFile = csv.writer(open("newLinks.csv", 'wb'))
headers = ["begin_node_id","end_node_id","length","speed","time"]
linkFile.writerow(headers)
for nodeTuple in allStreets:
	newArr = [nodeTuple[0].id, nodeTuple[1].id, nodeTuple[0].distanceConnections[nodeTuple[1]], nodeTuple[0].speedConnections[nodeTuple[1]], nodeTuple[0].timeConnections[nodeTuple[1]]]
	linkFile.writerow(newArr)
