import csv
from node import getInitialNodes

#Based off of the gridRegions, writes to the node CSV file the gridRegion
gridOfNodes = getInitialNodes(20, 10)
dictOfNodes = dict()
i = 0
for column in gridOfNodes:
	j = 0
	for gridRegion in column:
		for node in gridRegion.nodes:		
			dictOfNodes[node.id] = 20 * i + j
		j += 1
	i += 1
listOfNodes = []
nodeFile = csv.reader(open("nodes.csv", 'rb'))
header = True
i =0 
for node in nodeFile:
	if header:
		header = False
		continue
	currNode = list(node)
	currRegion = dictOfNodes[currNode[0]]
	if len(currNode) == 10:
		currNode.append(currRegion)
	else:
		currNode[10] = currRegion
	listOfNodes.append(currNode)
	i += 1
nodeFile = csv.writer(open("nodes.csv", 'wb'))
headers = ["node_id","is_complete","num_in_links","num_out_links","osm_traffic_controller","xcoord","ycoord",
"osm_changeset","birth_timestamp","death_timestamp","grid_region_id"]
nodeFile.writerow(headers)
for node in listOfNodes:
	nodeFile.writerow(node)

