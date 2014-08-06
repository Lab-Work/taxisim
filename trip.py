class trip:

#WHAT AN ARRAYFROMCSV CONSISTS OF 
#medallion,tripSeconds,trip_distance,pickup_longitude,pickup_latitude,dropoff_longitude,dropoff_latitude,startNodeID,endNodeID

	def __init__(self, arrFromCSV):
		self.medallion	= arrFromCSV[0]
		self.tripTime	= float(arrFromCSV[1])
		self.tripDist 	= float(arrFromCSV[2])
		self.startLong 	= float(arrFromCSV[3])
		self.startLat 	= float(arrFromCSV[4])
		self.endLong 	= float(arrFromCSV[5])
		self.endLat 	= float(arrFromCSV[6])
		self.startNode 	= float(arrFromCSV[7])
		self.endNode 	= float(arrFromCSV[8])

		#The number of trips that this trip used to be before it was condensed
		self.numTrips	= float(arrFromCSV[9])

		#The list of nodes traversed in order between the startNode and endNode
		self.nodeList	= []

		#A dictionary that, given the street ID (startNode.id, endNode.id), will return the two nodes (startNode, endNode)
		self.nodeDict	= dict()

		#How long the trip is estimated last
		self.estTime 	= 0
