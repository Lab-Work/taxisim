from node import node, getNodeRange
from math import sqrt
from grid import gridRegion, setUpGrid
from trip import trip
import Queue
import csv

#USES A COMBINATION OF A* AND ARCFLAGS TO ROUTE FROM ONE PLACE TO ANOTHER (ALSO FINDS START AND END NODES)

#Standard Euclidean distance multiplied given our region of space (NYC), where I converted it to a plane using Spherical -> cartesian coordinates.
def distance(lat1, long1, lat2, long2):
	diffLat = float(lat1) - float(lat2)
	diffLong = float(long1) - float(long2)
	latMiles = diffLat * 111194.86461 #meters per degree latitude, an approximation  based off our latitude and longitude
	longMiles = diffLong * 84253.1418965 #meters per degree longitude, an approximation  based off our latitude and longitude
	return sqrt(latMiles * latMiles + longMiles * longMiles)

def heuristic(connectedNode, endNode, fastestSpeed):
	return distance(connectedNode.lat, connectedNode.long, endNode.lat, endNode.long)/fastestSpeed

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
				if currDistance < bestDistance and len(node.distanceConnections) > 0:
					bestNode = node
					bestDistance = currDistance
	return bestNode

#Every node in array nodes gets reset so it has no distance from anything, no time from anything, and came from nothing (used to reset after making the path)
def resetNodes(arrNodes):
	for node in arrNodes:
		if node != None:
			node.cameFrom = None
			node.bestTime = float("INF")

def arcFlags(startLong, startLat, endLong, endLat, gridOfNodes, nodeInfo, N, fastestSpeed):
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
	nodesToSearch.put((0, startNode))
	nodesToSearch2 = set()
	nodesToSearch2.add(startNode)
	startNode.bestTime = 0
	while not nodesToSearch.empty():
		#Gets the node closest to the end node in the best case
		currNode = nodesToSearch.get()[1]
		searchedNodes.add(currNode)
#		nodesToSearch2.remove(currNode)

		#End of the path - we found it! Now we just need to reset all the nodes so they are at their default (no distance, no 			camefrom)
		if currNode == endNode:
			#This returns a list of Nodes, in order of traversal (finalPath[0] = startNode, finalPath[len(finalPath) - 1] = endNode)
			finalPath = rebuildPath(currNode)
			resetNodes(nodesToSearch2)
			resetNodes(searchedNodes)
			return finalPath
		for connectedNode in currNode.speedConnections:
			#THE ARCFLAGS PORTION
			if currNode.isArcFlags[connectedNode][endNode.region] == 0:
				if currNode.region != endNode.region:
					continue

			#If we've searched it before or it is nonexistant, continue
			if currNode.timeConnections[connectedNode] <= 0:
				continue
			if connectedNode in searchedNodes:
				continue

			#Checks distance thus far and the best case distane between this point and the endpoint
			tentativeBestSoFar = float(currNode.timeConnections[connectedNode]) + currNode.bestTime

			#If we haven't queued it up to search yet, queue it up now. Otherwise, for both of the next two if statements, place the best 				path we've found thus far into that node
			if tentativeBestSoFar < connectedNode.bestTime:
				connectedNode.cameFrom = currNode
				connectedNode.bestTime = tentativeBestSoFar
				nodesToSearch.put((heuristic(connectedNode, endNode, fastestSpeed) + connectedNode.bestTime, connectedNode))
				nodesToSearch2.add(connectedNode)
	print startNode.id
	print endNode.id
	resetNodes(nodesToSearch2)
	resetNodes(searchedNodes)
	return "No Path Found"

#Given where the nodes came from, rebuilds the path that was taken to the final node
def rebuildPath(node):
	arr = []
	while node != None:
		arr.append(node)
		node = node.cameFrom
	return arr[::-1]



