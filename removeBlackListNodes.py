import csv

def removeBlacklist():
	nodeFile = csv.reader(open("nodes.csv", 'rb'))
	listOfNodes = []
	for row in nodeFile:
		listOfNodes.append(row)
	finalListOfNodes = []
	blackList = csv.reader(open("Blacklist.csv", 'r'))
	setOfBlacklist = set()
	for row in blackList:
		setOfBlacklist.add(row[2])
	i = 0
	for node in listOfNodes:
		if i == 0 or node[0] not in setOfBlacklist:
			finalListOfNodes.append(node)
		i += 1
	nodeFile = csv.writer(open("nodes.csv", 'wb'))
	for row in finalListOfNodes:
		nodeFile.writerow(row)

if __name__ == '__main__':
	removeBlacklist()
