import csv
from grid import setUpGrid, gridRegion
from removeBlackListNodes import removeBlacklist

#TODO: REMOVE THE DUPLICATE STUFF TAKING INTO ACCOUNT NONES

#A vertex in our map (edge class not used -> simply used lists within the node)
class node:

	def __init__(self, ID, LAT, LONG, REGION):
		self.id = ID
		self.lat = float(LAT)
		self.long = float(LONG)
		self.region = int(REGION)
		
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
		self.isBackwardsArcFlags = {}

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
		self.timeConnections[ID] = float(weight)/float(speed)

	def setArcFlags(self, ID, hexString):
		newList = hexDeconverter(hexString)
		self.isArcFlags[ID] = newList

	def addBackwardsNode(self, ID, weight):
		self.backwardsConnections[ID] = float(weight)

	#Sets all of the streets to that initial speed
	def setSpeedConnections(self, initSpeed):
		for connection in self.distanceConnections:
			self.speedConnections[connection] = initSpeed
			self.timeConnections[connection] = self.distanceConnections[connection] / initSpeed

	def findMinBoundaryTime(self):
		return min(self.timeFromBoundaryNode)

#For converting the regions in the arcFlags csv file back into binary from hex
def hexDeconverter(hexString):
	newString = bin(int(hexString, 16))[2:]
	newList = map(int, list(newString))
	if len(newList) < 400:
		newList = [0] * (400 - len(newList)) + newList
	return newList

#############################
#		NON ARC FLAG		#
#############################

#Instead of them distanceConnections using ID's as the keys, they use actual Nodes. Also sets up boundary nodes and arcflags
def fixNodes(dictOfNodes, hasSpeeds, hasArcFlags):
	for ID in dictOfNodes:
		currNode = dictOfNodes[ID]
		newConnections = {}
		speedConnections = {}
		timeConnections = {}
		arcFlags = {}
		
		for connectingNodeID in currNode.distanceConnections:
			try:
				newNode = dictOfNodes[connectingNodeID]
				if newNode != -1:
					#The new way is pass in a node, instead of the ID
					newConnections[newNode] = currNode.distanceConnections[connectingNodeID]
					speedConnections[newNode] = currNode.speedConnections[connectingNodeID]
					timeConnections[newNode] = currNode.timeConnections[connectingNodeID]
					
					#Set isArcFlags[newNode] = secondDict{}
					#secondDict[RegionNumber] = True or False
					if hasArcFlags == None:
						currNode.isArcFlags[newNode] = False
					else:
						arcFlags[newNode] = currNode.isArcFlags[connectingNodeID]
			except(KeyError):
				pass
		currNode.distanceConnections = newConnections
		currNode.speedConnections = speedConnections
		currNode.timeConnections = timeConnections
		if hasArcFlags != None:
			currNode.isArcFlags = arcFlags

	for nodeID in dictOfNodes:
		node = dictOfNodes[nodeID]
		for connectingNode in node.timeConnections:
			connectingNode.backwardsConnections[node] = node.timeConnections[connectingNode]
			if connectingNode.region != node.region:
				connectingNode.isBoundaryNode = True

#Returns a set of nodes with all their distanceConnections properly set
def setUpNodes(timeFile, arcFlagFile):
	dictOfLinks = dict()
	allLinks = csv.reader(open("links.csv", 'rb'), delimiter = ',')
	speedOfLinks = None
	if timeFile != None:
		speedOfLinks = csv.reader(open(timeFile, 'rb'), delimiter = ',')
	arcFlags = None
	if arcFlagFile != None:
		arcFlags = csv.reader(open(arcFlagFile, 'rb'), delimiter = ',')	
	#Dictionary should be startNodeID -> setOfAllLinks that have that startNode
	header = True
	for link in allLinks:
		if header:
			header = False
			continue
		if link[1] in dictOfLinks:
			dictOfLinks[link[1]].append(link)
		else:
			dictOfLinks[link[1]] = []
			dictOfLinks[link[1]].append(link)
	#Key is startNode, list of all streets that start at that node
	header = True
	#Key is startNode, adds speeds of links
	if speedOfLinks != None:
		for link in speedOfLinks:
			if header:
				header = False
				continue
			currList = dictOfLinks[link[0]]
			for origLink in currList:
				#If the endNodes are the same (streets are the same)
				if origLink[2] == link[1]:
					origLink.append(link[3]) #Speed of link
					origLink.append(link[4]) #Time of link
	header = True
	#Key is startNode, adds arcLinks
	if arcFlags != None:
		for link in arcFlags:
			if header:
				header = False
				continue
			currList = dictOfLinks[link[0]]
			for origLink in currList:
				#If the endNodes are the same (streets are the same)
				if origLink[2] == link[1]:
					origLink.append(link[2])
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
					if link[2] != newNode.id and len(link) == 19 and float(link[17]) > 0:	
						newNode.addConnectingNode(link[2], link[5], link[16], link[17])
						newNode.setArcFlags(link[2], link[18])
					if link[2] != newNode.id and len(link) == 18 and float(link[17]) > 0:	
						newNode.addConnectingNode(link[2], link[5], link[16], link[17])
					if link[2] != newNode.id and len(link) == 16:
						newNode.addConnectingNode(link[2], link[5], 5, float(link[5])/5)
			except(KeyError):
				pass
			dictOfNodes[newNode.id] = newNode
		counter += 1
	#Changes what they connections keys are (from node ID's to nodes)
	fixNodes(dictOfNodes, speedOfLinks, arcFlags)
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

#If no arcFlags, arcFlagFile == None
def getCorrectNodes(numDivisions, timeFile, arcFlagFile):
	nodes = setUpNodes(timeFile, arcFlagFile)
	if timeFile == None:
		for node in nodes:
			for connection in node.speedConnections:
				node.speedConnection[connection] = 5
				node.timeConnection[connection] = node.distanceConnection[connection]/5
	nodeInfo = getNodeInfo(nodes)
	return setUpGrid(nodeInfo[0] + .01, nodeInfo[1], nodeInfo[2] + .01, nodeInfo[3], numDivisions, nodes)

#Returns an array that goes like this
#[MaxLat, MinLat, MaxLong, MinLong]
def getNodeRange(gridOfNodes):
	nodeInfo = [-1000, 1000, -1000, 1000]
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
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

if __name__ == "__main__":
	print "Running"
	getCorrectNodesArcs(20, "speeds_per_hour/0_0" ,"arcFlags/20Regions0_0.csv")
