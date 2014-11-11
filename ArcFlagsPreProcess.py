from Node import get_correct_nodes
from DijkstrasAlgorithm import DijkstrasAlgorithm
import csv
import timeit


# Pre-process the map with arc flags.
class ArcFlagsPreProcess:
    # Resets the arcflag set in dijkstras algorithm
    @staticmethod
    def reset_arc_flags(grid_of_nodes):
        for column in grid_of_nodes:
            for region in column:
                for node in region.nodes:
                    for connection in node.is_forward_arc_flags:
                        node.is_forward_arc_flags[connection] = False

    # Converts an arcflag binary string to hexadecimal so that it can be stored
    # in text easier
    @staticmethod
    def convert_to_hex(list_of_arcs):
        final_string = ""
        for i in range(0, len(list_of_arcs), 4):
            value_to_hex = 8 * list_of_arcs[i] + 4 * list_of_arcs[i + 1] + (
                2 * list_of_arcs[i + 2] + list_of_arcs[i + 3])
            final_string += str(hex(value_to_hex))[-1:]
        return final_string

    @staticmethod
    def run(map_file):
        grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/" + map_file,
                                          None)
        i = 0
        dictionary_of_arc_flags = dict()
        fastest_velocity = 0
        for column in grid_of_nodes:
            for grid_region in column:
                for node in grid_region.nodes:
                    for conn in node.is_forward_arc_flags:
                        dictionary_of_arc_flags[
                            (str(node.node_id), str(conn.node_id))] = [0] * 400
                    for link in node.forward_links:
                        if link.speed > fastest_velocity:
                            fastest_velocity = link.speed
        start = timeit.default_timer()
        for column in grid_of_nodes:
            for grid_region in column:  # one grid to test
                print "Next Region!"
                if i % 10 == 0:
                    stop = timeit.default_timer()
                    print stop - start
                set_of_nodes = set()
                # Makes sure set_of_nodes only contains the boundary nodes
                for node in grid_region.nodes:
                    if node.is_boundary_node:
                        set_of_nodes.add(node)

                start = timeit.default_timer()
                # Does a multi-dijkstra search to get an arcflag tree
                warmstart = True
                use_domination_value = False
                DijkstrasAlgorithm.dijkstra(set_of_nodes, grid_of_nodes,
                                            warmstart, use_domination_value)
                for column in grid_of_nodes:
                    for grid_region in column:
                        for node in grid_region.nodes:
                            for conn in node.is_forward_arc_flags:
                                if node.is_forward_arc_flags[conn]:
                                    # A new arcFlag entry - start_node,
                                    # end_node, region, arcflags go to
                                    dictionary_of_arc_flags[(
                                        str(node.node_id), str(conn.node_id))][i] = 1
                ArcFlagsPreProcess.reset_arc_flags(grid_of_nodes)
                i += 1
                break  # debug - only process one grid
            break  # debug - only process one grid
        stop = timeit.default_timer()  # debug - only process one grid
        print "Running time:", stop - start, "seconds"  # debug

        link_file = csv.writer(open("ArcFlags/map_"+map_file+".csv", 'wb'))
        # This is a hexadecimal string that converts region to true or false
        headers = ["start_nodeID", "end_nodeID", "hexStringOfRegions"]
        # RegionNumber   = 0, 1, 2, 3, 4, 5, 6, 7
        # is_forward_arc_flags   = 0, 1, 1, 0, 1, 1, 0, 1
        # HexString      = 6D

        link_file.writerow(headers)
        for key in dictionary_of_arc_flags:
            curr_list = dictionary_of_arc_flags[key]
            hex_string = ArcFlagsPreProcess.convert_to_hex(curr_list)
            new_arr = []
            new_arr.append(key[0])
            new_arr.append(key[1])
            new_arr.append(hex_string)
            link_file.writerow(new_arr)


if __name__ == '__main__':
    ArcFlagsPreProcess.run("0_0")
