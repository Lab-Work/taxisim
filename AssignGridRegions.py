import csv
from Node import get_correct_nodes

# Based off of the gridRegions, writes to the node CSV file the grid_region
grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)
dist_of_nodes = dict()
# Iterates through every region / node and assigns them a number
i = 0
for column in grid_of_nodes:
    j = 0
    for grid_region in column:
        for node in grid_region.nodes:
            dist_of_nodes[node.id] = 20 * i + j
        j += 1
    i += 1
# Will contain all the normal CSV info for the nodes, plus a region number
list_of_nodes = []
node_file = csv.reader(open("nyc_map4/nodes.csv", 'rb'))
header = True
for node in node_file:
    if header:
        # If it is the first row, we ignore it
        header = False
        continue
    curr_node = list(node)
    curr_region = dist_of_nodes[curr_node[0]]
    if len(curr_node) == 10:
        curr_node.append(curr_region)
    else:
        # In case the node has an extra element, which occasionally happened
        curr_node[10] = curr_region
    list_of_nodes.append(curr_node)
node_file = csv.writer(open("nyc_map4/newNodes.csv", 'wb'))
headers = ["node_id", "is_complete", "num_in_links", "num_out_links",
           "osm_traffic_controller", "xcoord", "ycoord", "osm_changeset",
           "birth_timestamp", "death_timestamp", "grid_region_id"]
node_file.writerow(headers)
for node in list_of_nodes:
    node_file.writerow(node)
