from node import get_correct_nodes
from dijkstrasAlgorithm import dijkstra
import csv
import timeit


# Resets the arcflag set in dijkstra's algorithm
def reset_arc_flags(grid_of_nodes):
    for _column in grid_of_nodes:
        for region in _column:
            for _node in region.nodes:
                for _connection in _node.is_arc_flags:
                    _node.is_arc_flags[_connection] = False


# Converts an arcflag binary string to hexadecimal so that it can be stored in text easier
def convert_to_hex(list_of_arcs):
    final_string = ""
    for k in range(0, len(list_of_arcs), 4):
        value_to_hex = 8 * list_of_arcs[k] + 4 * list_of_arcs[k + 1] + 2 * list_of_arcs[k + 2] + \
                       list_of_arcs[k + 3]
        final_string += str(hex(value_to_hex))[-1:]
    return final_string


_grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)
currSet = set()
i = 0
dictionaryOfArcFlags = dict()
fastestVelocity = 0
for column in _grid_of_nodes:
    for grid_region in column:
        for node in grid_region.nodes:
            for connection in node.is_arc_flags:
                dictionaryOfArcFlags[(str(node.id), str(connection.id))] = [0] * 400
                if node.speed_connections[connection] > fastestVelocity:
                    fastestVelocity = node.speed_connections[connection]
start = timeit.default_timer()
for column in _grid_of_nodes:
    for grid_region in column:
        print "Next Region!"
        if i % 10 == 0:
            stop = timeit.default_timer()
            print stop - start
        set_of_nodes = set()
        # Makes sure setOfNodes only contains the boundaryNodes
        for node in grid_region.nodes:
            if node.is_boundary_node:
                set_of_nodes.add(node)

        start = timeit.default_timer()
        # Does a multi-dijkstra search to get an arcflag tree
        dijkstra(set_of_nodes, _grid_of_nodes)
        for col in _grid_of_nodes:
            for _grid_region in col:
                for node in _grid_region.nodes:
                    for connection in node.is_arc_flags:
                        if node.is_arc_flags[connection]:
                            # A new arcFlag entry - startNode, endNode, region arcflags go to)
                            dictionaryOfArcFlags[(str(node.id), str(connection.id))][i] = 1
        reset_arc_flags(_grid_of_nodes)
        i += 1
link_file = csv.writer(open("arcFlags/20Regions0_0.csv", 'wb'))
# This is a hexadecimal string that converts region to true or false
headers = ["startNodeID", "endNodeID", "hexStringOfRegions"]
# RegionNumber = 0, 1, 2, 3, 4, 5, 6, 7
#is_arc_flags   = 0, 1, 1, 0, 1, 1, 0, 1
#HexString      = 6D

link_file.writerow(headers)
for key in dictionaryOfArcFlags:
    curr_list = dictionaryOfArcFlags[key]
    hex_string = convert_to_hex(curr_list)
    new_arr = [key[0], key[1], hex_string]
    link_file.writerow(new_arr)
