from node import getCorrectNodes
from dijkstrasAlgorithm import dijkstra
import csv
import timeit
import time

#Resets the arcflag set in dijkstras algorithm
def resetArcFlags(gridOfNodes):
	for column in gridOfNodes:
		for region in column:
			for node in region.nodes:
				for connection in node.isArcFlags:
					node.isArcFlags[connection] = False

#Converts an arcflag binary string to hexadecimal so that it can be stored in text easier
def convertToHex(listOfArcs):
	finalString = ""
	for i in range(0, len(listOfArcs), 4):
		valueToHex = 8 * listOfArcs[i] + 4 * listOfArcs[i + 1] + 2 * listOfArcs[i + 2] + listOfArcs[i + 3]
		finalString += str(hex(valueToHex))[-1:]
	return finalString
		

gridOfNodes = getCorrectNodes(20, "speeds_per_hour/0_0", None)
currSet = set()
i = 0
dictionaryOfArcFlags = dict()
fastestVelocity = 0
for column in gridOfNodes:
	for gridRegion in column:
		for node in gridRegion.nodes:
			for connection in node.isArcFlags:
				dictionaryOfArcFlags[(str(node.id), str(connection.id))] = [0] * 400
				if node.speedConnections[connection] > fastestVelocity:
					fastestVelocity = node.speedConnections[connection]
start = timeit.default_timer()
for column in gridOfNodes:
	for gridRegion in column:
		print "Next Region!"
		if i % 10 == 0:
			stop = timeit.default_timer()
			print stop - start
		setOfNodes = set()
		#Makes sure setOfNodes only contains the boundaryNodes
		for node in gridRegion.nodes:
			if node.isBoundaryNode:
				setOfNodes.add(node)
	
		start = timeit.default_timer()
		#Does a multi-dijkstra search to get an arcflag tree
		dijkstra(setOfNodes, gridOfNodes)
		for column in gridOfNodes:
			for gridRegion in column:
				for node in gridRegion.nodes:
					for connection in node.isArcFlags:
						if node.isArcFlags[connection]:
							#A new arcFlag entry - startNode, endNode, region arcflags go to)
							dictionaryOfArcFlags[(str(node.id), str(connection.id))][i] = 1
		resetArcFlags(gridOfNodes)
		i += 1
linkFile = csv.writer(open("arcFlags/20Regions0_0.csv", 'wb'))
headers = ["startNodeID", "endNodeID", "hexStringOfRegions"] #This is a hexadecimal string that converts region to true or false 
#RegionNumber = 0, 1, 2, 3, 4, 5, 6, 7
#isArcFlags   = 0, 1, 1, 0, 1, 1, 0, 1
#HexString	  = 6D

linkFile.writerow(headers)
for key in dictionaryOfArcFlags:
	currList = dictionaryOfArcFlags[key]
	hexString = convertToHex(currList)
	newArr = []
	newArr.append(key[0])
	newArr.append(key[1])
	newArr.append(hexString)
	linkFile.writerow(newArr)
