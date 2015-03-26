from Node import get_correct_nodes
from DijkstrasAlgorithm import DijkstrasAlgorithm
import csv
import timeit
from Map import Map
from db_functions import db_arc_flags
from db_functions import db_main
from datetime import datetime



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
        start = timeit.default_timer()
        for region_id in range(nyc_map.total_region_count):
            print "Next Region!"
            if i % 10 == 0:
                stop = timeit.default_timer()
                print stop - start

            boundary_nodes = nyc_map.get_region_boundary_nodes(region_id)

            start = timeit.default_timer()
            # Does a multi-origin bidirectional dijkstra search to get an
            # arcflag tree
            warmstart = True
            use_domination_value = False
            DijkstrasAlgorithm.bidirectional_dijkstra(boundary_nodes,
                                                      nyc_map,
                                                      warmstart,
                                                      use_domination_value)
            i += 1
        stop = timeit.default_timer()  # debug - only process one grid
        print "Running time:", stop - start, "seconds"  # debug
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
