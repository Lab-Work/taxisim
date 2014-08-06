from node import node
from grid import gridRegion, setUpGrid
import Queue
import csv
import timeit

#Assigns each Boundary node an index in the list
def initializeDictionary(listOfBoundaryNodes):
	i = 0
	dictOfIndices = dict()
	for node in listOfBoundaryNodes:
		dictOfIndices[node] = i
		i += 1
	return dictOfIndices

#Sets up lists of "INF" for each nodes, excluding boundary nodes
def initializeNodes(dictOfIndices, listOfBoundaryNodes, gridOfNodes):
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
				#Each node needs a distance from each boundary node, all starting at infinity
				node.timeFromBoundaryNode = [float("INF")] * len(listOfBoundaryNodes)
				node.arcFlagPaths = [None] * len(listOfBoundaryNodes)
				try:
					#If it's in the dictionary, it's a boundary node, and thus must be 0 away from itself
					index = dictOfIndices[node]
					node.timeFromBoundaryNode[index] = 0
					node.wasUpdated.add(index)
				except(KeyError):
					pass

def distanceDictionary(dictOfIndices, listOfBoundaryNodes, gridOfNodes):
	distDict = dict()
	for boundNode in listOfBoundaryNodes:
		index = dictOfIndices[boundNode]
		for column in gridOfNodes:
			for region in column:
				for node in region.nodes:
					distDict[(boundNode.id, node.id)] = node.timeFromBoundaryNode[index]
	return distDict

#Every node in array nodes gets reset so it has no distance from anything, no time from anything, and came from nothing (used to reset after making the path)
def resetNodes(arrNodes):
	for node in arrNodes:
		if node != None:
			node.cameFrom = None
			node.bestTime = float("INF")
			node.arcFlagPaths = []
			node.timeFromBoundaryNodes = []

#Basically creates a tree rooted at the boundary node where every edge in the tree is an arcflag
def dijkstra(listOfBoundaryNodes, gridOfNodes):
	#Assign each boundary node an index for distance
	dictOfIndices = initializeDictionary(listOfBoundaryNodes)

	#Gives each node a distance from the boundary nodes, which are initially either INF(inity) or 0
	initializeNodes(dictOfIndices, listOfBoundaryNodes, gridOfNodes)

	#Nodes we intend to search (somehow connected to graph so far). We treat this as a priority queue: the one that has the potential to 		be closest (has best distance from the startNode/is closest to the endNode) is treated next
	nodesToSearch = Queue.PriorityQueue()

	#Checks to see if the node is already in the queue (True means it is in it, False means it is not)
	for node in listOfBoundaryNodes:
		nodesToSearch.put((0, node))
		node.inQueue = True
	 
	i = 0
	while not nodesToSearch.empty():
		#Gets the node closest to the end node in the best case
		i += 1
		if i % 10000 == 0:
			print nodesToSearch.qsize()
		currNode = nodesToSearch.get()[1]
		currNode.inQueue = False
		for connectedNode in currNode.backwardsConnections:
			for index in currNode.wasUpdated:
				if connectedNode.timeConnections[currNode] <= 0:
					continue

				#Checks distance thus far and the best case distane between this point and the endpoint
				tentativeBestSoFar = float(connectedNode.timeConnections[currNode]) + currNode.timeFromBoundaryNode[index]

				#If we haven't queued it up to search yet, queue it up now. Otherwise, for both of the next two if statements, place the 					best path we've found thus far into that node
				if tentativeBestSoFar < connectedNode.timeFromBoundaryNode[index]:
					connectedNode.wasUpdated.add(index)
					connectedNode.arcFlagPaths[index] = currNode
					connectedNode.timeFromBoundaryNode[index] = tentativeBestSoFar
					if not connectedNode.inQueue:
						nodesToSearch.put((connectedNode.findMinBoundaryTime(), connectedNode))
						connectedNode.inQueue = True
		currNode.wasUpdated = set()
	distDict = distanceDictionary(dictOfIndices, listOfBoundaryNodes, gridOfNodes)
	setArcFlags(gridOfNodes)
	return distDict

#Given where the nodes came from, rebuilds the path that was taken to the final node
def setArcFlags(gridOfNodes):
	for column in gridOfNodes:
		for gridRegion in column:
			for node in gridRegion.nodes:
				for connection in node.arcFlagPaths:
					if connection != None:
						node.isArcFlags[connection] = True
			resetNodes(gridRegion.nodes)
