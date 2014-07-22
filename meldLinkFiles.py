from node import *
import csv

#2011-05-08

#Once you have the new link data (speed and such), this is how you merge the old data with the new data!

oldLinks = csv.reader(open("links.csv", 'rb'))
speedLinks = csv.reader(open("newLinks.csv", 'rb'))
oldLinksDict = dict()

for row in oldLinks:
	oldLinksDict[(row[1], row[2])] = row

for row in speedLinks:
	currList = oldLinksDict[(row[0], row[1])]
	currList.append(row[3])
	currList.append(row[4])
	oldLinksDict[(row[0], row[1])] = currList

newFile = csv.writer(open("newLinksX.csv", 'wb'))
headers = "link_id,begin_node_id,end_node_id,begin_angle,end_angle,street_length,osm_name,osm_class,osm_way_id,startX,startY,endX,endY,osm_changeset,birth_timestamp,death_timestamp,speed,time".split(',')
newFile.writerow(headers)
for key in oldLinksDict:
	if key == ("begin_node_id","end_node_id"):
		continue
	#Because we blacklist the nodes and not the links, there are a few links that have no node counterparts and therefore will not get a 		speed or time. We assign it the speed/time -1, -1 here.
	if len(oldLinksDict[key]) == 16:
		oldLinksDict[key].append(-1)
		oldLinksDict[key].append(-1)
	newFile.writerow(oldLinksDict[key])
