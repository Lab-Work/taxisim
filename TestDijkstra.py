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
class TestArcFlags:
    # Resets the arcflag set in dijkstras algorithm
    @staticmethod
    def reset_arc_flags(grid_of_nodes):
        for column in grid_of_nodes:
            for region in column:
                for node in region.nodes:
                    for connection in node.is_arc_flags:
                        node.is_arc_flags[connection] = False

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
    def output_labels(grid_of_nodes, outfile, boundary_indices):
        print "outputting"
        output_table = []
        for column in grid_of_nodes:
            for grid_region in column:
                for node in grid_region.nodes:
                    output_table.append([node.id] + node.time_from_boundary_node)
        
        output_table.sort(key = lambda x: x[0])
        with open(outfile, "w") as f:
            w = csv.writer(f)
            sorted_nodes = sorted(boundary_indices, key = lambda x: boundary_indices[x])
            node_ids = [n.id for n in sorted_nodes]            
            w.writerow(["Node"] + node_ids)            
            
            for row in output_table:
                w.writerow(row)
            
        

    @staticmethod
    def run(map_file, outfile, warmstart=True):

        grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/" + map_file,
                                          None)
    
        grid_region = grid_of_nodes[10][10]

        set_of_nodes = set()
        # Makes sure set_of_nodes only contains the boundary nodes
        for node in grid_region.nodes:
            if node.is_boundary_node:
                set_of_nodes.add(node)


        start_time = datetime.now()

        boundary_indices = DijkstrasAlgorithm.dijkstra(set_of_nodes, grid_of_nodes, warmstart)
        
        print datetime.now() - start_time

        TestArcFlags.output_labels(grid_of_nodes, outfile, boundary_indices)

    @staticmethod
    def runIndependently(map_file, outfile):
        grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/" + map_file,
                                          None)
    
        grid_region = grid_of_nodes[10][10]

        set_of_nodes = set()
        # Makes sure set_of_nodes only contains the boundary nodes
        for node in grid_region.nodes:
            if node.is_boundary_node:
                set_of_nodes.add(node)


        start_time = datetime.now()

        boundary_indices = DijkstrasAlgorithm.independentDijkstra(set_of_nodes, grid_of_nodes)
        
        print datetime.now() - start_time

        TestArcFlags.output_labels(grid_of_nodes, outfile, boundary_indices)
        
        
if __name__ == '__main__':
    #TestArcFlags.runIndependently("0_0", "nodes_independent.csv")
    #TestArcFlags.run("0_0", "nodes_minkey_coldstart.csv", False)
    TestArcFlags.run("0_0", "nodes_minkey_warmstart.csv", True)
