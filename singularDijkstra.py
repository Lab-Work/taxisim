from node import node
from grid import gridRegion, setUpGrid
import Queue
import csv
import timeit
import time

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

#Every node in array nodes gets reset so it has no distance from anything, no time from anything, and came from nothing (used to reset after making the path)
def resetNodes(arrNodes):
	for node in arrNodes:
		if node != None:
			node.cameFrom = None
			node.bestTime = float("INF")
			node.arcFlagPaths = []
			node.timeFromBoundaryNodes = []

#Basically creates a tree rooted at the boundary node where every edge in the tree is an arcflag
def singularDijkstra(distDict, boundaryNode, gridOfNodes):
	#Keeps track of all the nodes we have completeed
	searchedNodes = set()

	#Nodes we intend to search (somehow connected to graph so far). We treat this as a priority queue: the one that has the potential to 		be closest (has best distance from the startNode/is closest to the endNode) is treated next
	nodesToSearch = Queue.PriorityQueue()
	nodesInQueue = set()	

	nodesToSearch.put((0, boundaryNode))
	nodesInQueue.add(boundaryNode)

	boundaryNode.bestTime = 0
	while not nodesToSearch.empty():
		#Gets the node closest to the end node in the best case
		currNode = nodesToSearch.get()[1]
		for connectedNode in currNode.backwardsConnections:
			if connectedNode.timeConnections[currNode] <= 0:
				continue
			if connectedNode in searchedNodes:
				continue

			#Checks distance thus far and the best case distane between this point and the endpoint
			tentativeBestSoFar = float(connectedNode.timeConnections[currNode]) + currNode.bestTime

			#If we haven't queued it up to search yet, queue it up now. Otherwise, for both of the next two if statements, place the 				best path we've found thus far into that node
			if tentativeBestSoFar < connectedNode.bestTime:
				connectedNode.cameFrom = currNode
				connectedNode.bestTime = tentativeBestSoFar
				if not connectedNode in nodesInQueue:
					nodesToSearch.put((connectedNode.bestTime, connectedNode))
					connectedNode.inQueue = True
	compareArcFlags(distDict, boundaryNode, gridOfNodes)
	for column in gridOfNodes:
		for region in column:
			resetNodes(region.nodes)

def compareArcFlags(distDict, boundaryNode, gridOfNodes):
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
				if node.bestTime != distDict[(boundaryNode.id, node.id)]:
					print "ERROR!: Single(" + str(node.bestTime) + "), Multiple(" +str(distDict[(boundaryNode.id, node.id)]) + ")"
