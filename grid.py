class gridRegion:

	#A square region with latitude and longitude coordinates bounding it, as well as every node within it.
	def __init__(self, upBound, lowBound, rightBound, leftBound):
		self.up = upBound
		self.down = lowBound
		self.left = leftBound
		self.right = rightBound
		self.nodes = set()

#Given an overall area and how many regions you want (numDivisions x numDivisions), will return a list of gridRegions that make up the overall map and put all the nodes necessary in each gridRegion from listOfNodes
def setUpGrid(upMost, downMost, rightMost, leftMost, numDivisions, listOfNodes):
	grid = []
	#The height and width of each grid region
	changeInLat = (upMost - downMost)/float(numDivisions)
	changeInLong = (rightMost - leftMost)/float(numDivisions)
	currLeft = leftMost
	#Left-Right
	for i in range(numDivisions):
		#Each subList represents  a bunch of grid regions within some longitudal constraint
		currDown = downMost
		thisLong = []
		for j in range(numDivisions):
			#We are creating a new gridRegion
			newRegion = gridRegion(currDown + changeInLat, currDown, currLeft + changeInLong, currLeft)
			thisLong.append(newRegion)
			currDown += changeInLat
		grid.append(thisLong)
		currLeft += changeInLong
	for node in listOfNodes:
		#The coordinates hashed into the grid based off the node's lat and long
		i = int(float(node.long - leftMost) / float(changeInLong))
		j = int(float(node.lat - downMost) / float(changeInLat))
		grid[i][j].nodes.add(node)
	return grid

