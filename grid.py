#TODO: COMMENT THE SHIT OUT OF THIS

class gridRegion:

	#A square region with latitude and longitude coordinates bounding it, as well as every node within it.
	def __init__(self, upBound, lowBound, rightBound, leftBound):
		self.up = upBound
		self.down = lowBound
		self.left = leftBound
		self.right = rightBound
		#TODO: Make it a set of Nodes
		self.nodes = []

#Given an overall area and how many regions you want (numDivisions x numDivisions), will return a list of gridRegions that make up the overall map and put all the nodes necessary in each gridRegion from listOfNodes
def setUpGrid(upMost, downMost, rightMost, leftMost, numDivisions, listOfNodes):
	grid = []
	changeInLat = (upMost - downMost)/float(numDivisions)
	changeInLong = (rightMost - leftMost)/float(numDivisions)
	currLeft = leftMost
	#Left-Right
	for i in range(numDivisions):
		#Up-Down
		currDown = downMost
		thisLong = []
		for j in range(numDivisions):
			newRegion = gridRegion(currDown + changeInLat, currDown, currLeft + changeInLong, currLeft)
			thisLong.append(newRegion)
			currDown += changeInLat
		grid.append(thisLong)
		currLeft += changeInLong
	for node in listOfNodes:
		i = int(float(node.long - leftMost) / float(changeInLong))
		j = int(float(node.lat - downMost) / float(changeInLat))
		grid[i][j].nodes.append(node)
	return grid

