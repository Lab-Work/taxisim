import csv

from node import getSetOfNodes

#This entire thing is an implementation of Kosaraju's Algorithm for finding strongly connected components. If there are weakly connected components we would like to rid ourselves of them
#http://en.wikipedia.org/wiki/Kosaraju%27s_algorithm

#A stack object
class stack:

	def __init__(self):
		self.s = []
		self.set = set()
		self.latestElementIndex = -1

	def push(self, obj):
		self.latestElementIndex += 1
		self.set.add(obj)
		if len(self.s) == self.latestElementIndex:
			self.s.append(obj)
		else:
			self.s[self.latestElementIndex] = obj

	def lastElem(self):
		return self.s[self.latestElementIndex]

	def pop(self):
		obj = self.s[self.latestElementIndex]
		self.s[self.latestElementIndex] = -1
		self.latestElementIndex -= 1
		self.set.discard(obj)
		return obj

	def existsIn(self, obj):
		return (obj in self.set)

	def size(self):
		return self.latestElementIndex + 1

	def resetNodes(self):
		for node in self.s:
			node.discovered = False


def getFirstFalse(setOfNodes):
	i = 0
	for node in setOfNodes:
		if node.discovered == False:
			return node
		i += 1
	return None

#An implementation of DFS, whether on the transpose graph or the actual graph
def DFS(node, STACK, transpose):
	node.discovered = True
	tempStack = stack()
	tempStack.push(node)
	if transpose == False:
		while tempStack.size() != 0:
			currNode = tempStack.lastElem()
			for connection in currNode.distanceConnections:
				if connection.discovered == False:
					connection.discovered = True
					tempStack.push(connection)
			if currNode == tempStack.lastElem():
				STACK.push(tempStack.pop())
	else:
		while tempStack.size() != 0:
			currNode = tempStack.lastElem()
			for connection in currNode.backwardsConnections:
				if connection.discovered == False:
					connection.discovered = True
					tempStack.push(connection)
			if currNode == tempStack.lastElem():
				STACK.push(tempStack.pop())

def resetNodes(setOfNodes):
	for node in setOfNodes:
		node.discovered = False

newFile = open("Blacklist.csv", 'wb')
newFileWriter = csv.writer(newFile)
headers = ["SubgraphNumber", "Type", "NodeID", "FromLong", "FromLat","ToLong", "ToLat","Color"]
newFileWriter.writerow(headers)

#All nodes in NYC
setOfNodes = getSetOfNodes()
stackOfNodes = stack()
node = getFirstFalse(setOfNodes)

#This is a depth first search upon the graph -> The moment one node terminates, it is added to the stack. If component terminates, it will continue on to the next component until all components terminate.
while node != None:
	DFS(node, stackOfNodes, False)
	node = getFirstFalse(setOfNodes)

#We set every node to undiscovered again
stackOfNodes.resetNodes()
resetNodes(setOfNodes)
subGraphNumber = 0

#The latter part of of Kosaraju's algorithm. We perform a DFS upon each object, starting at the top of the stack. Once that particular DFS terminates, we know that is a strongly connected component and write it to the CSV file (all under the same subgraph number).
while stackOfNodes.size() != 0:
	currNode = stackOfNodes.pop()
	if currNode.discovered == True:
		continue
	DFSStack = stack()
	DFS(currNode, DFSStack, True)

	#We assume for New York City that most components are connected (More than 90%). Thus, for our ~ 100000 nodes, all non strongly 	connected components will be of size < 10000
	if DFSStack.size() < 10000:
		while DFSStack.size() != 0:
			node = DFSStack.pop()
			newArr = [subGraphNumber, "node", node.id, node.long, node.lat, 0, 0, "red"]
			newFileWriter.writerow(newArr)
			for connection in node.distanceConnections:
				newArr = [subGraphNumber, "link", node.id, node.long, node.lat, connection.long, connection.lat, "black"]
				newFileWriter.writerow(newArr)
	subGraphNumber += 1
