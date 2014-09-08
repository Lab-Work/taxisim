import csv
from node import getCorrectNodes

#Based off of the gridRegions, writes to the node CSV file the gridRegion
gridOfNodes = getCorrectNodes(20, "speeds_per_hour/0_0", None)
dictOfNodes = dict()
#Iterates through every region / node and assigns them a number
i = 0
for column in gridOfNodes:
	j = 0
	for gridRegion in column:
		for node in gridRegion.nodes:		
			dictOfNodes[node.id] = 20 * i + j
		j += 1
	i += 1
#Will contain all the normal CSV info for the nodes, plus a region number
listOfNodes = []
nodeFile = csv.reader(open("nodes.csv", 'rb'))
header = True
for node in nodeFile:
	if header:
		#If it is the first row, we ignore it
		header = False
		continue
	currNode = list(node)
	currRegion = dictOfNodes[currNode[0]]
	if len(currNode) == 10:
		currNode.append(currRegion)
	else:
		#In case the node has an extra element, which occasionally happened
		currNode[10] = currRegion
	listOfNodes.append(currNode)
nodeFile = csv.writer(open("nodes.csv", 'wb'))
headers = ["node_id","is_complete","num_in_links","num_out_links","osm_traffic_controller","xcoord","ycoord",
"osm_changeset","birth_timestamp","death_timestamp","grid_region_id"]
nodeFile.writerow(headers)
for node in listOfNodes:
	nodeFile.writerow(node)

