Taxisim - A Library for Traffic Estimation, Mapping, and Routing using GPS data
================================================================================

##1) Overview
This library contains code for performing analysis of vehicle GPS data on urban road networks.  Specifically, it contains traffic estimation algorithms, graph partitioning and preprocessing algorithms, efficient routing algorithms including Bidirectional Dijkstra's, Bidirectional A\* and Bidirectional ArcFlags, integration with PostgreSQL database systems, and a framework for performing large-scale parallel analyses using **mpi4py**.  The library is designed to work with maps loaded from OpenStreetMap via [AwesomeStitch](https://github.com/Lab-Work/AwesomeStitch). This document serves as a quick-start for those wishing to use any of the included code.  The purpose is to describe the purpose and usage of various modules and files within this library.


##2)License


This software is licensed under the *University of Illinois/NCSA Open Source License*:

**Copyright (c) 2013 The Board of Trustees of the University of Illinois. All rights reserved**

**Developed by: Department of Civil and Environmental Engineering University of Illinois at Urbana-Champaign**

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal with the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimers. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimers in the documentation and/or other materials provided with the distribution. Neither the names of the Department of Civil and Environmental Engineering, the University of Illinois at Urbana-Champaign, nor the names of its contributors may be used to endorse or promote products derived from this Software without specific prior written permission.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE SOFTWARE.

##3) Modules / Folders

### [/routing](routing)
Includes all of the code relating to loading, representing, and processing road network graphs, and performing shortest-path routing queries on them.  Specifically, it can:
- Load/save road networks from/to CSV files, using the same format as AwesomeStitch
- Efficiently match coordinates to the nearest node in the graph using a KD-Tree
- Partition road networks using a KD-Tree
- Partition road networks using the [KaHip](https://github.com/schulzchristian/KaHIP/) library.  KaHip needs to be downloaded and compiled before these particular functions work.
- Generate figures that show the color-coded partitioning results
- Identify strongly-connected components using kosajaru's algorithm, and prune the graph down to one large strongly-connected component
- Efficiently erform shortest-path routing queries using Bidirectional Dijkstra's algorithm, Bidirectional A\*, and Bidirectional ArcFlags
- Perform the preprocessing steps which are necessary for ArcFlags

### [/traffic_estimation](traffic_estimation)
All code relating to estimating traffic conditions from taxi GPS data.  Specifically, it is designed to estimate the travel times on links of the road network, even when the data only contains origins, destinations, and total travel times.  In other words, no intermediate way-points or paths are required - they are estimated simultaneously with the traffic conditions.  Specifically, this module can:
- Estimate the traffic conditions from GPS data
- Perform cross-validation experiments to quantify the prediction accuracy
- Produce graphics which show the estimated traffic conditions

### [/db_functions](db_functions)
This module allows the code connect to a PostgreSQL database for saving/loading data and results.  Specifically, it can:
- Load taxi trips (which contain GPS coordinates, times, etc.) from the database
- Load and save traffic estimates (i.e. travel times on each link) into the database.  Travel times are indexed by the date/time that they occured, since they generally change over time
- Load and save ArcFlags, which are produced in the [/routing](routing) module.  These are also indexed by the date/time, since the ArcFlags depend on the traffic conditions, which change over time.

### [/mpi_parallel](mpi_parallel)
This module is built on top of **mpi4py**.  It contains a convenient framework for performing large-scale parallel tasks on supercomputers.  The basic idea is similar to the **map** portion of a map-reduce operation - it applies the same function to a large set of inputs at the same time.  The usage is similar to Python's built-in **map** or **multiprocessing.Pool.map()*.  However, it is specialized to quickly disseminate data that is used by all of the workers.  The reason behind this is that many of the applications of parallel processing in this library use the *same* road network in each instance.


### [/nyc_map4](nyc_map4)
Not a module - contains a sample map of New York City, which can be used with the remainder of the code.  The data format is explained below:

**node.csv:**

1. node_id - a unique identifier for each node
2. is_complete
3. num_in_links - the number of incoming links to this node
4. num_out_links - the number f outgoing links from this node
5. osm_traffic_controller
6. xcoord - the longitude of this node
7. ycoord - the latitude of this node
8. osm_changeset - the changeset ID from OSM
9. birth_timestamp - the time this node was loaded by AwesomeStitch
10. death_timestamp - the time this node was deleted in AwesomeStitch
11. region_id


**links.csv:**

1. link_id
2. begin_node_id
3. end_node_id
4. begin_angle
5. end_angle
6. street_length
7. osm_name
8. osm_class
9. osm_way_id
10. startX
11. startY
12. endX
13. endY
14. osm_changeset
15. birth_timestamp
16. death_timestamp




##4) Files





