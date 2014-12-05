# -*- coding: utf-8 -*-
"""
Created on Sat Oct 25 14:18:17 2014

@author: brian
"""

from Node import get_correct_nodes
from DijkstrasAlgorithm import DijkstrasAlgorithm
import csv
from datetime import datetime


# Pre-process the map with arc flags.
class TestDijkstra:

    # Outputs all of the labels computed by DijkstrasAlgorithm to file
    # These labels contain each node's distance from each origin(boundary_nodes
    # for a specific region)
    # params:
        # grid_of_nodes - a list of list of GridRegions-see get_correct_nodes()
        # boundary_nodes - the set of boundary nodes for a specific region
        # outfile - the name of the file to save the results in
    @staticmethod
    def output_labels(grid_of_nodes, boundary_nodes, outfile):
        print "outputting forward graph"
        # create one row for each node
        output_table = []
        for column in grid_of_nodes:
            for grid_region in column:
                for node in grid_region.nodes:
                    output_table.append([node.node_id] +
                                        list(node.forward_boundary_time))

        # sort the rows and write them to CSV file
        output_table.sort(key=lambda x: x[0])

        outfile = "test_output/forward" + outfile
        with open(outfile, "w") as f:
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
        for column in grid_of_nodes:
            for grid_region in column:
                for node in grid_region.nodes:
                    output_table.append([node.node_id] +
                                        list(node.backward_boundary_time))

        # sort the rows and write them to CSV file
        output_table.sort(key=lambda x: x[0])

        outfile = "test_output/backward" + outfile
        with open(outfile, "w") as f:
            w = csv.writer(f)
            sorted_nodes = sorted(boundary_nodes,
                                  key=lambda x: x.boundary_node_id)
            node_ids = [n.node_id for n in sorted_nodes]
            w.writerow(["Node"] + node_ids)

            for row in output_table:
                w.writerow(row)

    @staticmethod
    def run(grid_of_nodes, region_i, region_j, outfile, warmstart=True,
            use_domination_value=False):

        # Reset important quantities before we run DijkstrasAlgorithm
        DijkstrasAlgorithm.reset_nodes(grid_of_nodes)

        # get the boundary nodes for this region
        boundary_nodes = grid_of_nodes[region_i][region_j].get_boundary_nodes()

        # Run Dijkstra's algorithm with multiple origins and time it
        start_time = datetime.now()
        DijkstrasAlgorithm.bidirectional_dijkstra(boundary_nodes,
                                                  grid_of_nodes,
                                                  warmstart,
                                                  use_domination_value)
        print datetime.now() - start_time

        TestDijkstra.output_labels(grid_of_nodes, boundary_nodes, outfile)

    @staticmethod
    def runIndependently(grid_of_nodes, region_i, region_j, outfile):

        # Reset important quantities before we run DijkstrasAlgorithm
        DijkstrasAlgorithm.reset_nodes(grid_of_nodes)

        # get the boundary nodes for this region
        boundary_nodes = grid_of_nodes[region_i][region_j].get_boundary_nodes()

        # Run Dijkstra's algorithm with each origin independently and time it
        start_time = datetime.now()
        DijkstrasAlgorithm.independent_dijkstra(boundary_nodes, grid_of_nodes)
        print datetime.now() - start_time

        TestDijkstra.output_labels(grid_of_nodes, boundary_nodes, outfile)

if __name__ == '__main__':
    # Load the map
    grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)

    # These are some regions that we will compute
    regions_of_interest = [(0, 0), (10, 10), (11, 5), (17, 6), (16, 4),
                           (19, 18), (17, 3), (18, 2)]

    # For each of the regions, compute the answer using several variations on
    # Dijkstras algorithm
    # Performance and correctness can be compared
    for (i, j) in regions_of_interest:
        print ("================================== PROCESSING REGION " +
               str((i, j)) + " =================================")
        print
        print("---------Independent")
        TestDijkstra.runIndependently(grid_of_nodes, i, j, "nodes_" + str(i) + "_" + str(j) + "_independent.csv")
        # print("---------Minkey Cold")
        # TestDijkstra.run(grid_of_nodes, i, j, "nodes_" + str(i) + "_" + str(j) + "_minkey_coldstart.csv", False, False)
        print("---------Minkey Warm")
        TestDijkstra.run(grid_of_nodes, i, j, "nodes_" + str(i) +
                         "_" + str(j) + "_minkey_warmstart.csv", True, False)
        # print("---------Domkey Cold")
        # TestDijkstra.run(grid_of_nodes, i, j, "nodes_" + str(i) + "_" + str(j) + "_domkey_coldstart.csv", False, True)
        # print("---------Domkey Warm")
        # TestDijkstra.run(grid_of_nodes, i, j, "nodes_" + str(i) + "_" + str(j) + "_domkey_warmstart.csv", True, True)

