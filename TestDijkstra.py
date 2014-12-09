# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 14:18:17 2014

@author: brian
"""

from Node import get_correct_nodes
from DijkstrasAlgorithm import DijkstrasAlgorithm
import csv
from datetime import datetime
from Map import Map


# Pre-process the map with arc flags.
class TestDijkstra:

    # Outputs all of the labels computed by DijkstrasAlgorithm to file
    # These labels contain each node's distance from each origin(boundary_nodes
    # for a specific region)
    # params:
        # nyc_map - a map containing regions
        # boundary_nodes - the set of boundary nodes for a specific region
        # outfile - the name of the file to save the results in
    @staticmethod
    def output_labels(nyc_map, boundary_nodes, outfile):
        print "outputting forward graph"
        # create one row for each node
        output_table = []

        for node in nyc_map.nodes:
            output_table.append([node.node_id] +
                                list(node.forward_boundary_time))

        # sort the rows and write them to CSV file
        output_table.sort(key=lambda x: x[0])

        forward_outfile = "test_output/forward" + outfile
        with open(forward_outfile, "w") as f:
            w = csv.writer(f)
            sorted_nodes = sorted(boundary_nodes,
                                  key=lambda x: x.boundary_node_id)
            node_ids = [n.node_id for n in sorted_nodes]
            w.writerow(["Node"] + node_ids)

            for row in output_table:
                w.writerow(row)

        print "outputting backward graph"
        # create one row for each node
        output_table = []

        for node in nyc_map.nodes:
            output_table.append([node.node_id] +
                                list(node.backward_boundary_time))

        # sort the rows and write them to CSV file
        output_table.sort(key=lambda x: x[0])

        backward_outfile = "test_output/backward" + outfile
        with open(backward_outfile, "w") as f:
            w = csv.writer(f)
            sorted_nodes = sorted(boundary_nodes,
                                  key=lambda x: x.boundary_node_id)
            node_ids = [n.node_id for n in sorted_nodes]
            w.writerow(["Node"] + node_ids)

            for row in output_table:
                w.writerow(row)

    @staticmethod
    def run(nyc_map, region_id, outfile, warmstart=True,
            use_domination_value=False):

        # Reset important quantities before we run DijkstrasAlgorithm
        DijkstrasAlgorithm.reset_nodes(nyc_map)

        # get the boundary nodes for this region
        boundary_nodes = nyc_map.get_region_boundary_nodes(region_id)

        # Run Dijkstra's algorithm with multiple origins and time it
        start_time = datetime.now()
        DijkstrasAlgorithm.bidirectional_dijkstra(boundary_nodes,
                                                  nyc_map,
                                                  warmstart,
                                                  use_domination_value)
        print datetime.now() - start_time

        TestDijkstra.output_labels(nyc_map, boundary_nodes, outfile)

    @staticmethod
    def runIndependently(nyc_map, region_id, outfile):

        # Reset important quantities before we run DijkstrasAlgorithm
        DijkstrasAlgorithm.reset_nodes(nyc_map)

        # get the boundary nodes for this region
#         boundary_nodes = grid_of_nodes[region_i][region_j].get_boundary_nodes()
        boundary_nodes = nyc_map.get_region_boundary_nodes(region_id)

        # Run Dijkstra's algorithm with each origin independently and time it
        start_time = datetime.now()
        DijkstrasAlgorithm.independent_dijkstra(boundary_nodes, nyc_map)
        print datetime.now() - start_time

        TestDijkstra.output_labels(nyc_map, boundary_nodes, outfile)

if __name__ == '__main__':
    # Load the map
#     grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)

    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    nyc_map.assign_node_regions()


    # These are some regions that we will compute
    regions_of_interest = [0, 5, 10, 11, 17, 18, 19]

    # For each of the regions, compute the answer using several variations on
    # Dijkstras algorithm
    # Performance and correctness can be compared
    for i in regions_of_interest:
        print ("================================== PROCESSING REGION " +
               str(i) + " =================================")
        print
        print("---------Independent")
        TestDijkstra.runIndependently(
            nyc_map,
            i,
            "nodes_" +
            str(i) +
            "_independent.csv")
        """
        print("---------Minkey Cold")
        TestDijkstra.run(nyc_map, i, j, "nodes_" + str(i) + "_" + str(j)
                         + "_minkey_coldstart.csv", False, False)
        """
        print("---------Minkey Warm")
        TestDijkstra.run(nyc_map, i, "nodes_" + str(i) +
                         "_minkey_warmstart.csv", True, False)
        """
        print("---------Domkey Cold")
        TestDijkstra.run(nyc_map, i, j, "nodes_" + str(i) + "_" + str(j)
                         + "_domkey_coldstart.csv", False, True)
        print("---------Domkey Warm")
        TestDijkstra.run(nyc_map, i, j, "nodes_" + str(i) + "_" + str(j)
                         + "_domkey_warmstart.csv", True, True)
        """
