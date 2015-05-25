Taxisim - A Library for Traffic Estimation, Mapping, and Routing using GPS data
================================================================================

##1) Overview
This library contains code for performing analysis of vehicle GPS data on urban road networks.  Specifically, it contains traffic estimation algorithms, graph partitioning and preprocessing algorithms, efficient routing algorithms including Bidirectional Dijkstra's, Bidirectional A\* and Bidirectional ArcFlags, integration with PostgreSQL database systems, and a framework for performing large-scale parallel analyses using **mpi4py**.  This document serves as a quick-start for those wishing to use any of the included code.  The purpose is to describe the purpose and usage of various modules and files within this library.  The next section gives the free software license, and the remaining sections each explain one module.

##2)License


This software is licensed under the *University of Illinois/NCSA Open Source License*:

**Copyright (c) 2013 The Board of Trustees of the University of Illinois. All rights reserved**

**Developed by: Department of Civil and Environmental Engineering University of Illinois at Urbana-Champaign**

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal with the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimers. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimers in the documentation and/or other materials provided with the distribution. Neither the names of the Department of Civil and Environmental Engineering, the University of Illinois at Urbana-Champaign, nor the names of its contributors may be used to endorse or promote products derived from this Software without specific prior written permission.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH THE SOFTWARE.








node.csv: 

0 - node_id
1 - is_complete
2 - num_in_links
3 - num_out_links
4 - osm_traffic_controller
5 - xcoord
6 - ycoord
7 - osm_changeset
8 - birth_timestamp
9 - death_timestamp
10 - grid_region_id


links.csv:

0 - link_id
1 - begin_node_id
2 - end_node_id
3 - begin_angle
4 - end_angle
5 - street_length
6 - osm_name
7 - osm_class
8 - osm_way_id
9 - startX
10  - startY
11 - endX
12 - endY
13 - osm_changeset
14 - birth_timestamp
15  - death_timestamp
