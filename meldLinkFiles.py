import csv

# Once you have the new link data (speed and time), this is how you merge the
# old data with the new data!

old_links = csv.reader(open("links.csv", 'rb'))
speed_links = csv.reader(open("newLinks.csv", 'rb'))
old_links_dict = dict()

for row in old_links:
    old_links_dict[(row[1], row[2])] = row

for row in speed_links:
    curr_list = old_links_dict[(row[0], row[1])]
    curr_list.append(row[3])
    curr_list.append(row[4])
    old_links_dict[(row[0], row[1])] = curr_list

new_file = csv.writer(open("newLinksX.csv", 'wb'))
headers = ("link_id,begin_node_id,end_node_id,begin_angle,end_angle," +
           "street_length,osm_name,osm_class,osm_way_id,startX,startY,endX," +
           "endY,osm_changeset,birth_timestamp,death_timestamp," +
           "speed,time").split(',')
new_file.writerow(headers)
for key in old_links_dict:
    if key == ("begin_node_id", "end_node_id"):
        continue
    # Because we blacklist the nodes and not the links, there are a few links
    # that have no Node counterparts and therefore will not get a speed or time
    # We assign it the speed/time -1, -1 here.
    if len(old_links_dict[key]) == 16:
        old_links_dict[key].append(-1)
        old_links_dict[key].append(-1)
    new_file.writerow(old_links_dict[key])
