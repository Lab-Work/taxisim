from node import getInitialNodes
from dijkstrasAlgorithm import dijkstra
from singularDijkstra import singularDijkstra
import csv

#Resets the arcflag set in dijkstras algorithm
def resetArcFlags(gridOfNodes):
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
				for connection in node.isArcFlags:
					node.isArcFlags[connection] = False

linkFile = csv.writer(open("arcFlags/20Regions.csv", 'wb'))
headers = ["beginNode", "endNode", "regionNumber"]
linkFile.writerow(headers)
gridOfNodes = getInitialNodes(20, 10)
currSet = set()
i = 0
setOfTuples = set()
for column in gridOfNodes:
	for gridRegion in column:
		print "Next Region!"
		setOfNodes = set()
		for node in gridRegion.nodes:
			if node.isBoundaryNode:
				setOfNodes.add(node)
		distDict = dijkstra(setOfNodes, gridOfNodes)
		for column in gridOfNodes:
			for gridRegion in column:
				for node in gridRegion.nodes:
					for connection in node.isArcFlags:
						if node.isArcFlags[connection]:
							#A new arcFlag entry - startNode, endNode, region arcflags go to)
							newEntry = [node.id, connection.id, i]
							linkFile.writerow(newEntry)
		resetArcFlags(gridOfNodes)
		i += 1
