from Node import get_correct_nodes
from DijkstrasAlgorithm import DijkstrasAlgorithm
import csv
import timeit
from Map import Map
from db_functions import db_arc_flags
from db_functions import db_main
from datetime import datetime
from traffic_estimation import plot_estimates



# Pre-process the map with arc flags.
class ArcFlagsPreProcess:
    # Resets the arcflag set in dijkstras algorithm

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
    def run(region_size = 250):
        nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv",
                      lookup_kd_size=1, region_kd_size=region_size,
                      limit_bbox=Map.reasonable_nyc_bbox)
        nyc_map.assign_node_regions()
        nyc_map.assign_link_arc_flags()

        #nyc_map.save_region("../nyc_map4/region.csv")
        db_main.connect("db_functions/database.conf")
        #get_correct_nodes(nyc_map, "../speeds_per_hour/" + map_file, None)
        db_arc_flags.create_arc_flag_table()

        i = 0
        print nyc_map.total_region_count
        for region_id in range(nyc_map.total_region_count):
            # print "Next Region!"

            boundary_nodes = nyc_map.get_region_boundary_nodes(region_id)

            # Does a multi-origin bidirectional dijkstra search to get an
            # arcflag tree
            warmstart = True
            use_domination_value = False
            DijkstrasAlgorithm.bidirectional_dijkstra(boundary_nodes,
                                                      nyc_map,
                                                      warmstart,
                                                      use_domination_value)
            #####################################################################
            # DRAW ARC_FLAGS USING THIS
            # pace_dict = {}
            # for link in nyc_map.links:
            #     if link.backward_arc_flags_vector[i] == True:
            #         pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5
            #     else:
            #         pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5
            # plot_estimates.plot_speed(nyc_map, "Backward Arc Flags Region: " + str(i), "Backward"+str(i), pace_dict)

            # pace_dict = {}
            # for link in nyc_map.links:
            #     if link.forward_arc_flags_vector[i] == True:
            #         pace_dict[(link.origin_node_id, link.connecting_node_id)] = 5
            #     else:
            #         pace_dict[(link.origin_node_id, link.connecting_node_id)] = -5

            # plot_estimates.plot_speed(nyc_map, "Forward Arc Flags Region: " + str(i), "Forward"+str(i), pace_dict)

            #####################################################################
            i += 1


        d = datetime(2012,3,5,2)
        db_arc_flags.save_arc_flags(nyc_map, d)


        db_main.close()
        # This is a hexadecimal string that converts region to true or false
        # RegionNumber           = 0, 1, 2, 3, 4, 5, 6, 7
        # is_forward_arc_flags   = 0, 1, 1, 0, 1, 1, 0, 1
        # HexString              = 6D

        # TODO: print backward arc flags


if __name__ == '__main__':
    ArcFlagsPreProcess.run("0_0")
