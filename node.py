import csv
from grid import setUpGrid, gridRegion
from removeBlackListNodes import removeBlacklist

#TODO: INITIALIZE SPEEDS/TIMES GIVEN BY A CSV FILE

#A vertex in our map (edge class not used -> simply used lists within the node)
class node:

	def __init__(self, ID, LAT, LONG, REGION):
		self.id = ID
		self.lat = float(LAT)
		self.long = float(LONG)
		self.region = REGION
		
		#Used during the route calculator -> this keeps track of the node previous to this one in a path
		#i.e. If the path was A->C->B->D, B.cameFrom == C
		self.cameFrom = None

		#Used for DFS
		self.discovered = False
		
		#Keeps track of how far away we are from the startNode
		self.bestTime = float("INF")

		#These are nodes that are connected by edges that start at the current node and their weights
		self.distanceConnections = {}
		self.backwardsConnections = {} #Measured in meters
		self.speedConnections = {}
		self.timeConnections = {}
		self.isArcFlags = {}

		##################################################
		#Used in multiple dijkstra arcflag precomputation#
		##################################################

		#Tells if the node is a boundary node	
		self.isBoundaryNode = False

		#During the dijkstra algorithm, give a set of which indices were updated
		self.wasUpdated = set()

		self.timeFromBoundaryNode = []

		#For each boundary node path, shows where this particular node came from		
		self.arcFlagPaths = []
	
		#Checks if the node is currently in the queue (won't add otherwise)
		self.inQueue = False
	
	#Given an ID, gives its weight
	def addConnectingNode(self, ID, weight, speed, time):
		self.distanceConnections[ID] = float(weight)
		self.speedConnections[ID] = float(speed)
		self.timeConnections[ID] = float(time)

	def addBackwardsNode(self, ID, weight):
		self.backwardsConnections[ID] = float(weight)

	#Sets all of the streets to that initial speed
	def setSpeedConnections(self, initSpeed):
		for connection in self.distanceConnections:
			self.speedConnections[connection] = initSpeed
			self.timeConnections[connection] = self.distanceConnections[connection] / initSpeed

	def findMinBoundaryTime(self):
		return min(self.timeFromBoundaryNode)

#Instead of them distanceConnections using ID's as the keys, they use actual Nodes. Also sets up boundary nodes and arcflags
def fixNodes(dictOfNodes):
	for ID in dictOfNodes:
		currNode = dictOfNodes[ID]
		newConnections = {}
		for connectingNodeID in currNode.distanceConnections:
			try:
				newNode = dictOfNodes[connectingNodeID]
				if newNode != -1:
					#The new way is pass in a node, instead of the ID
					newConnections[newNode] = currNode.distanceConnections[connectingNodeID]
					
					#Set isArcFlags[newNode] = secondDict{}
					#secondDict[RegionNumber] = True or False
					currNode.isArcFlags[newNode] = False
			except(KeyError):
				pass
		currNode.distanceConnections = newConnections
	for nodeID in dictOfNodes:
		node = dictOfNodes[nodeID]
		for connectingNode in node.distanceConnections:
			connectingNode.backwardsConnections[node] = node.distanceConnections[connectingNode]
			if connectingNode.region != node.region:
				connectingNode.isBoundaryNode = True

#Returns a set of nodes with all their distanceConnections properly set
def setUpNodes(timeFile):
	dictOfLinks = dict()
	allLinks = csv.reader(open("links.csv", 'rb'), delimiter = ',')
	speedOfLinks = csv.reader(open(timeFile, 'rb'), delimiter = ',')
	#Dictionary should be startNodeID -> setOfAllLinks that have that startNode
	for link in allLinks:
		try:
			dictOfLinks[link[1]].append(link)
		except(KeyError):
			dictOfLinks[link[1]] = []
			dictOfLinks[link[1]].append(link)
	for link in speedOfLinks:
		currList = dictOfLinks[link[0]]
		for origLink in currList:
			if origLink[2] == link[1]:
				origLink.append(link[3]) #Speed of link
				origLink.append(link[4]) #Time of link
	dictOfNodes = dict()
	allNodes = csv.reader(open("nodes.csv", 'rb'), delimiter = ',')
	counter = 0
	for aNode in allNodes:
		#Want to ignore the header line
		if counter != 0:
			#Creates the nodes and put them in the dictionary, with the ID as the key
			newNode = node(aNode[0], aNode[6], aNode[5], aNode[10])
			try:
				listOfLinks = dictOfLinks[newNode.id]
				for link in listOfLinks:
					if link[2] != newNode.id:	
						newNode.addConnectingNode(link[2], link[5])
			except(KeyError):
				pass
			dictOfNodes[newNode.id] = newNode
		counter += 1
	#Changes what they connections keys are (from node ID's to nodes)
	fixNodes(dictOfNodes)
	setOfNodes = set()
	for ID in dictOfNodes:
		setOfNodes.add(dictOfNodes[ID])
	return setOfNodes

#Returns an array that goes like this
#[MaxLat, MinLat, MaxLong, MinLong]
def getNodeInfo(arr):
	nodeInfo = [-1000, 1000, -1000, 1000]
	for node in arr:
		if float(node.lat) > nodeInfo[0]:
			nodeInfo[0] = float(node.lat)
		if float(node.lat) < nodeInfo[1]:
			nodeInfo[1] = float(node.lat)
		if float(node.long) > nodeInfo[2]:
			nodeInfo[2] = float(node.long)
		if float(node.long) < nodeInfo[3]:
			nodeInfo[3] = float(node.long)
	return nodeInfo

#Returns a set of all nodes
def getSetOfNodes():
	return setUpNodes()

#Gets all the nodes, but also gives them an initial velocity and time. This then sets it up in grid format and returns it
def getInitialNodes(numDivisions, initSpeed):
	nodes = setUpNodes()
	for node in nodes:
		node.setSpeedConnections(initSpeed)
	counter = 0
	nodeInfo = getNodeInfo(nodes)
	return setUpGrid(nodeInfo[0] + .01, nodeInfo[1], nodeInfo[2] + .01, nodeInfo[3], numDivisions, nodes)

def getCorrectNodes(numDivisions, timeFile):
	nodes = setUpNodes(timeFile)
	nodeInfo = getNodeInfo(nodes)
	return setUpGrid(nodeInfo[0] + .01, nodeInfo[1], nodeInfo[2] + .01, nodeInfo[3], numDivisions, nodes)


#Returns an array that goes like this
#[MaxLat, MinLat, MaxLong, MinLong]
def getNodeRange():
	nodes = getSetOfNodes()
	nodeInfo = [-1000, 1000, -1000, 1000]
	for node in nodes:
		if float(node.lat) > nodeInfo[0]:
			nodeInfo[0] = float(node.lat)
		if float(node.lat) < nodeInfo[1]:
			nodeInfo[1] = float(node.lat)
		if float(node.long) > nodeInfo[2]:
			nodeInfo[2] = float(node.long)
		if float(node.long) < nodeInfo[3]:
			nodeInfo[3] = float(node.long)
	nodeInfo[0] += .01
	nodeInfo[2] += .01
	return nodeInfo
