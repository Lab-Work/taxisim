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

### /routing

### /db_functions

### /traffic_estimation

### /mpi_parallel

### /nyc_map4
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





