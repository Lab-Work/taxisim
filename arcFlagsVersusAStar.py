from node import getCorrectNodes, getNodeRange
from arcFlags import arcFlags
from aStar import aStar
from trip import trip
import timeit
import csv

#This file is made for debugging purposes - meant to compare arcFlags to A* in terms of accuracy

readFrom = "../data_chron/FOIL2013/trip_04.csv"
N = 20
tripFile = csv.reader(open(readFrom, 'rb'))
i = 0
#Holds a set of random trips
allTrips = []
header = True
#Get 20000 trips
for t in tripFile:
	if header:
		#First row is just descriptions of data, not data at all
		header = False
		continue
	if i > 20000:
		break
	i += 1
	#This list is used to initialize a trip object
	newTripList = [t[0], t[8], t[9], float(t[10]), float(t[11]), float(t[12]), float(t[13]), -1, -1, 1]
	newTrip = trip(newTripList)
	allTrips.append(newTrip)
gridArcs = getCorrectNodes(N, "speeds_per_hour/0_0", "arcFlags/20Regions0_0.csv")
gridAStar = getCorrectNodes(N, "speeds_per_hour/0_0", None)
nodeInfo = getNodeRange(gridAStar)
fastestSpeed = 0 
#Iterates through every edge to find te fastest speed
for column in gridAStar:
	for region in column:
		for node in region.nodes:
			for connection in node.speedConnections:
				if node.speedConnections[connection] > fastestSpeed:
					fastestSpeed = node.speedConnections[connection]
allTripsArcs = []
allTripsStar = []
#Get all the aStar trips
#Get all the arcFlag trips and the time for both
start = timeit.default_timer()
for aTrip in allTrips:
	allTripsArcs.append(arcFlags(aTrip.startLong, aTrip.startLat, aTrip.endLong, aTrip.endLat, gridArcs, nodeInfo, N, fastestSpeed))
stop = timeit.default_timer()
print stop - start
i = 0
start = timeit.default_timer()
for aTrip in allTrips:
	allTripsStar.append(aStar(aTrip.startLong, aTrip.startLat, aTrip.endLong, aTrip.endLat, gridAStar, nodeInfo, N, fastestSpeed))
stop = timeit.default_timer()
print stop - start

tripFile = csv.writer(open("debugging_tools/aFVAS.csv", 'wb'))
headers = ["arcOrStar", "tripNumber", "startLat", "startLong", "endLat", "endLong"]
tripFile.writerow(headers)

#Compares the trips to ensure they are all the same
for i in range(len(allTripsArcs)):
	currTripArc = ""
	currTripStar = ""
	print i
	sumStar = 0
	sumArcs = 0
	#Writes to CSV files so we can use R later to print a graph
	for j in range(len(allTripsArcs[i]) - 1):
		currArc = allTripsArcs[i][j]
		nextArc = allTripsArcs[i][j + 1]
		sumArcs += currArc.timeConnections[nextArc]
		newRow = ["Arc", i, currArc.lat, currArc.long, nextArc.lat, nextArc.long]
		tripFile.writerow(newRow)
	for j in range(len(allTripsStar[i]) - 1):
		currStar = allTripsStar[i][j]
		nextStar = allTripsStar[i][j + 1]
		sumStar += currStar.timeConnections[nextStar]
		newRow = ["Star", i, currStar.lat, currStar.long, nextStar.lat, nextStar.long]
		tripFile.writerow(newRow)
	print sumArcs
	print sumStar
