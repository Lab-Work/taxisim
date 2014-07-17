from node import node, getInitialNodes, getNodeRange
from math import sqrt
from grid import gridRegion, setUpGrid
from trip import trip
import Queue
import csv
import timeit
import subprocess


#Standard Euclidean distance multiplied given our region of space (NYC), where I converted it to a plane using Spherical -> cartesian coordinates.
def distance(lat1, long1, lat2, long2):
	diffLat = float(lat1) - float(lat2)
	diffLong = float(long1) - float(long2)
	latMiles = diffLat * 111194.86461 #meters per degree latitude, an approximation  based off our latitude and longitude
	longMiles = diffLong * 84253.1418965 #meters per degree longitude, an approximation  based off our latitude and longitude
	return sqrt(latMiles * latMiles + longMiles * longMiles)



#Finds if a trip's data is out of bounds of our node data (nodes have region centered at (x,y)  with radius r_1, trips are sporadic)
def outOfBounds(LONG, LAT, NODEINFO):
	if LAT >= NODEINFO[0] or LAT < NODEINFO[1] or LONG >= NODEINFO[2] or LONG < NODEINFO[3]:
		return True
	return False

#Given a longitude and latitude, figures out which node is closest to it
def findNodes(LONG, LAT, gridOfNodes, NODEINFO, N):
	if outOfBounds(LONG, LAT, NODEINFO):
		print "OUT OF BOUNDS: (Long, Lat) = (" + str(LONG) + ", " + str(LAT) + ")"
		return None	
	#Node closest to coords and its distance
	bestNode = None
	bestDistance = 10000
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
				if currDistance < bestDistance and len(node.distanceConnections) > 0:
					bestNode = node
					bestDistance = currDistance
	return bestNode

#Every node in array nodes gets reset so it has no distance from anything and came from nothing (used to reset after making the path)
def resetNodes(arrNodes):
	for node in arrNodes:
		if node != None:
			node.cameFrom = None
			node.bestDistance = 0
			node.bestTime = 0

def aStar(startLong, startLat, endLong, endLat, gridOfNodes, nodeInfo, N, fastestSpeed):
	node1 = findNodes(startLong, startLat, gridOfNodes, nodeInfo, N)
	node2 = findNodes(endLong, endLat, gridOfNodes, nodeInfo, N)
	if node1 == None or node2 == None:
		print "COULDN'T FIND NODE"
		return 10000000
	return findShortestPath(node1, node2, fastestSpeed)

#Returns the shortest path between two nodes (Can modify to return the length instead, anything really) Using the A* algorithm
#http://en.wikipedia.org/wiki/A*_search_algorithm
def findShortestPath(startNode, endNode, fastestSpeed):

	#Nodes that we've already traversed and thus will not search again
	searchedNodes = set()

	#Nodes we intend to search (somehow connected to graph so far). We treat this as a priority queue: the one that has the potential to be closest (has best distance from the startNode/is closest to the endNode) is treated next
	nodesToSearch = Queue.PriorityQueue()
	nodesToSearch.put((startNode.bestTime, startNode))
	nodesToSearch2 = set()
	nodesToSearch2.add(startNode)
	while not nodesToSearch.empty():
		#Gets the node closest to the end node in the best case
		currNode = nodesToSearch.get()[1]
		searchedNodes.add(currNode)
		nodesToSearch2.remove(currNode)

		#End of the path - we found it! Now we just need to reset all the nodes so they are at their default (no distance, no 			camefrom)
		if currNode == endNode:
			#This returns a list of Nodes, in order of traversal (finalPath[0] = startNode, finalPath[len(finalPath) - 1] = endNode)
			finalPath = rebuildPath(currNode)
			resetNodes(nodesToSearch2)
			resetNodes(searchedNodes)
			return finalPath

		for connectedNode in currNode.speedConnections:

			#If we've searched it before or it is nonexistant, continue
			if connectedNode == -1:
				continue
			if connectedNode in searchedNodes:
				continue

			#Checks distance thus far and the best case distane between this point and the endpoint (note that someNode.bestDistance 				refers to the actual distance from the startNode, as opposed to Euclidean)
			tentativeBestSoFar = float(currNode.timeConnections[connectedNode]) + currNode.bestTime

			#If we haven't queued it up to search yet, queue it up now. Otherwise, for both of the next two if statements, place the best 				path we've found thus far into that node
			if not connectedNode in nodesToSearch2:
				connectedNode.cameFrom = currNode
				connectedNode.bestTime = tentativeBestSoFar
				#The heuristic here needs to be the shortest time possible, so we take the shortest distance (Euclidean) and divide it by 					the fastest possible street (the fastest velocity) 
				nodesToSearch.put((distance(connectedNode.lat, connectedNode.long, endNode.lat, endNode.long)/fastestSpeed + 										currNode.bestTime, connectedNode))
				nodesToSearch2.add(connectedNode)
			if tentativeBestSoFar < connectedNode.bestTime:
				connectedNode.cameFrom = currNode
				connectedNode.bestTime = tentativeBestSoFar
	print startNode.id
	print endNode.id
	resetNodes(nodesToSearch2)
	resetNodes(searchedNodes)
	return "No Path Found"

#Given where the nodes came from, rebuilds the path that was taken to the final node
def rebuildPath(node):
	arr = []
	while node.cameFrom != None:
		arr.append(node)
		node = node.cameFrom
	return arr[::-1]

if __name__ == "__main__":
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

	N = 22 
	fastestSpeed = 20 #meters per second
	initSpeed = 20 #meters per second
	gridOfNodes = getInitialNodes(N, initSpeed)
	nodeInfo = getNodeRange()
	fileReader = open("data.csv", 'wb')
	fileWriter = csv.writer(fileReader)
	headers = ["Type", "FromLon", "FromLat", "ToLon", "ToLat", "Color"]
	fileWriter.writerow(headers)
	tripsOfConcern = []
	i = 0
	for trip in tAgg:
		if i < 6:
			i += 1
			continue
		if i > 10:
			break
		print i
		path = aStar(trip.startLong, trip.startLat, trip.endLong, trip.endLat, gridOfNodes, nodeInfo, N, fastestSpeed)
		trip.nodeList = path
		tripsOfConcern.append(path)
		i += 1
	for path in tripsOfConcern:
		newArr = ["node", path[0].long, path[0].lat, 0, 0, "red"]
		fileWriter.writerow(newArr)
		newArr = ["node", path[len(path) - 1].long, path[len(path) - 1].lat, 0, 0, "red"]
		fileWriter.writerow(newArr)
		for i in range(len(path) - 1):
			newArr = ["link", path[i].long, path[i].lat, path[i + 1].long, path[i + 1].lat, "black"]
			fileWriter.writerow(newArr)


