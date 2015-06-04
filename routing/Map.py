from KDTree import KDTree
import csv
from Node import Node
from Link import Link
from traffic_estimation.Trip import Trip
from BiDirectionalSearch import bidirectional_search
from SCC import kosaraju
from datetime import datetime
from random import shuffle
import numpy as np


# Represents a roadmap, has a set of Nodes and Links


class Map:
    reasonable_nyc_bbox = (-74.05, 40.9, -73.85, 40.65)
    min_lat = float('inf')
    max_lat = float('-inf')
    min_lon = float('inf')
    max_lon = float('-inf')

    # Finds the Node which is nearest to a given coordinate.  Uses a KDTree for
    # fast lookup
    # Params:
    # lat - the query latitude
    # lon - the query longitude
    # LAT_METERS - one degree latitude equals this many meters
    # LON_METERS - one degree longitude equals this many meters (assume earth
    # is "flat enough")
    # Returns:
    # A Node object
    def get_nearest_node(
            self,
            lat,
            lon,
            LAT_METERS=111194.86461,
            LON_METERS=84253.1418965):
        if(lat < self.min_lat or lat > self.max_lat or lon < self.min_lon
           or lon > self.max_lon):
            return None
        # convert lat/lon to meters (approximate, assume NYC is flat)
        coordinates = (lat * LAT_METERS, lon * LON_METERS)
        node, dist = self.lookup_kd_tree.nearest_neighbor_query(coordinates)
        return node

    # Gets the region that a point is in geometrically
    # Params:
        # point - an array-like that contains coordinates(like a Node or tuple)
    # Returns: The region, which is a leaf node of the region_kd_tree
    def get_region(self, point):
        return self.region_kd_tree.get_leaf(point)

    def get_all_nodes_in_region(self, region_id):
        set_of_nodes = set()
        for node in self.nodes:
            if node.region_id == region_id:
                set_of_nodes.add(node)
        return set_of_nodes

    def get_region_boundary_nodes(self, region_id):
        nodes = self.get_all_nodes_in_region(region_id)
        boundary_nodes = []
        for node in nodes:
            if node.is_boundary_node:
                boundary_nodes.append(node)
        return boundary_nodes

    # Assigns integer region_id numbers to every node in the graph
    # Regions are based on the rectangular leaf nodes of the region_kd_tree

    def assign_link_arc_flags(self):
        for link in self.links:
            link.forward_arc_flags_vector = np.repeat(
                [False], self.total_region_count)
            link.backward_arc_flags_vector = np.repeat(
                [False], self.total_region_count)

    def assign_node_regions(self):
        print ("Region tree depth " + str(self.region_kd_tree.get_height()))
        region_id_lookup = {}
        next_region_id = 0

        for node in self.nodes:
            region = self.get_region(node)

            if(region not in region_id_lookup):
                region_id_lookup[region] = next_region_id
                next_region_id += 1

            node.region_id = region_id_lookup[region]

        self.total_region_count = next_region_id

        for node in self.nodes:
            for connecting_link in node.forward_links:
                connecting_node = connecting_link.connecting_node
                if connecting_node is None:
                    pass
                if connecting_node.region_id != node.region_id:
                    connecting_node.is_boundary_node = True
            for connecting_link in node.backward_links:
                connecting_node = connecting_link.origin_node
                if connecting_node is None:
                    pass
                if connecting_node.region_id != node.region_id:
                    connecting_node.is_boundary_node = True

        print "total regions : " + str(next_region_id)

    # Finds the maximum speed of any link in the graph
    def get_max_speed(self):
        max_speed = 0.0
        for link in self.links:
            link_speed = float(link.length) / link.time
            max_speed = max(max_speed, link_speed)
        return max_speed

    def get_default_speed(self):
        for link in self.links:
            link_speed = float(link.length) / link.time
            return link_speed
        return None

    def set_all_link_speeds(self, speed):
        for link in self.links:
            link.time = link.length / speed



    # An iterator function that returns the speeds of all links in list of lists format
    # Params:
        # num_trips_threshold - Only links with at least this many trips will be output
        # speed_dict - If supplied, speeds will be read from this dictionary instead of the map
            # the keys are of form (begin_node_id, connecting_node_id)
            # and the values are the speeds
    def get_pace_table(self, num_trips_threshold=0, pace_dict=None):
        yield ['start_node_id',
                             'end_node_id',
                             'start_lat',
                             'start_lon',
                             'end_lat',
                             'end_lon',
                             'pace',
                             'num_trips']
        
        if(pace_dict==None):
            # No speed dictionary supplied - read the speeds directly from the links
            for link in self.links:
                    if(link.time > 0 and link.num_trips >= num_trips_threshold):
                        pace = link.time / link.length
                        # pace is in seconds/meter
                        yield [link.origin_node.node_id,
                                         link.connecting_node.node_id,
                                         link.origin_node.lat,
                                         link.origin_node.long,
                                         link.connecting_node.lat,
                                         link.connecting_node.long,
                                         pace,
                                         link.num_trips]
        else:
            # Speed dict is supplied - read the speeds from the dictionary
            for link in self.links:
                if(link.origin_node!=None and link.connecting_node!=None):
                    key = (link.origin_node.node_id, link.connecting_node.node_id)
                    if(key in pace_dict):
                        pace = pace_dict[key]
                        # pace is in seconds/meter
                        yield [link.origin_node.node_id,
                                             link.connecting_node.node_id,
                                             link.origin_node.lat,
                                             link.origin_node.long,
                                             link.connecting_node.lat,
                                             link.connecting_node.long,
                                             pace,
                                             link.num_trips]
                        
        

    def save_speeds(self, filename, num_trips_threshold=0):
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            for line in self.get_speed_csv(num_trips_threshold):         
                writer.writerow(line)


    def save_region(self, filename):
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            color_map = {}
            colors = range(self.total_region_count)
            shuffle(colors)
            for node in self.nodes:
                if node.region_id in color_map:
                    node.color_id = color_map[node.region_id]
                else:
                    color = colors.pop()
                    color_map[node.region_id] = color
                    node.color_id = color

            writer.writerow(['node_id',
                             'lat',
                             'long',
                             'color_id'])
            for node in self.nodes:
                writer.writerow([node.node_id,
                                 node.lat,
                                 node.long,
                                 node.color_id])


    # Saves the map in CSV format, using two CSV files
    # Params:
        # node_filename - The CSV file to save the node data in
        # link_filename - The CSV file to save the link data in
    def save_as_csv(self, node_filename, link_filename):
        # First write node file
        with open(node_filename, 'w') as f:
            w = csv.writer(f)
            # Write header
            w.writerow(['node_id',
                'is_complete',
                'num_in_links',
                'num_out_links',
                'osm_traffic_controller',
                'longitude',
                'latitude',
                'osm_changeset',
                'birth_timestamp',
                'death_timestamp',
                'region_id'])
            # Write a row for each node
            for node in self.nodes:
                line = [node.node_id,
                     node.is_complete,
                     len(node.backward_links),  # num_in_links,
                     len(node.forward_links),  # num_out_links,
                     node.osm_traffic_controller,  # osm_traffic_controller,
                     node.long,
                     node.lat,
                     node.osm_changeset,  # osm_changeset,
                     node.birth_timestamp,  # birth_timestamp,
                     node.death_timestamp,  # death_timestamp,
                     node.region_id]
                w.writerow(line)
        
        # Next write link file
        with open(link_filename, 'w') as f:
            w = csv.writer(f)
            # First write header
            w.writerow(['link_id',
                'begin_node_id',
                'end_node_id',
                'begin_angle',
                'end_angle',
                'street_length',
                'osm_name',
                'osm_class',
                'osm_way_id',
                'startX',
                'startY',
                'endX',
                'endY',
                'osm_changeset',
                'birth_timestamp',
                'death_timestamp'])
            
            # Now write one row for each Link
            for link in self.links:
                if(link.origin_node!=None and link.connecting_node!=None):
                    line = [link.link_id,  # link_id,
                         link.origin_node.node_id,
                         link.connecting_node.node_id,
                         link.begin_angle,  # begin_angle,
                         link.end_angle,  # end_angle,
                         link.length,
                         link.osm_name,  # osm_name,
                         link.osm_class,
                         link.osm_way_id,  # osm_way_id,
                         link.origin_node.long,  # startX,
                         link.origin_node.lat,  # startY,
                         link.connecting_node.long,  # endX,
                         link.connecting_node.lat,  # endY,
                         link.osm_changeset,  # osm_changeset,
                         link.birth_timestamp,  # birth_timestamp,
                         link.death_timestamp]
                    w.writerow(line)
                 

    # Saves the graph in METIS file format    
    def save_as_metis(self, filename):
        #First, re-index nodes to start with 1
        n = len(self.nodes)
        new_node_ids = {}
        for i in xrange(n):
            new_node_ids[self.nodes[i].node_id] = i +1       
        
        linkset = set()
        
        for node in self.nodes:
            for link in node.forward_links:
                i = new_node_ids[node.node_id]
                j = new_node_ids[link.connecting_node.node_id]
                x = min(i,j)
                y = max(i,j)
                linkset.add((x,y))
            
        num_nodes = len(self.nodes)
        num_edges = len(linkset)
        
        
        with open(filename, 'w') as f:
            f.write("%d %d \n" % (num_nodes,num_edges) )
            # Write one line for each node
            for node in self.nodes:
                # Construct the set of neighbor node ids
                # Consisting of the forward and backward neighbors
                neighbors = set()
                neighbors.update([new_node_ids[link.connecting_node.node_id]
                                    for link in node.forward_links])
                neighbors.update([new_node_ids[link.origin_node.node_id]
                                    for link in node.backward_links])                      
                
                i = new_node_ids[node.node_id]
                for j in neighbors:
                    if((i,j) not in linkset and (j,i) not in linkset):
                        print("WTF")
                    
                
                
                # Sort them, convert to string, and write to file
                strs = map(str, sorted(neighbors))
                f.write(" ".join(strs) + "\n")
                
                
            
            
        

    # Builds the Map from CSV files describing the Nodes and LInks
    # Params:
        # nodes_fn - the name of the CSV file containing Node info
        # links_fn - the name of the CSV file containing Link info
        # lookup_id_size - the leaf_size for the Node lookup kd tree.  Should
        # be small for fastest performance
        # region_id_size - the leaf_size for the region kd tree.  Should be
        # large
        # limit_bbox - An optional bounding box for limiting the size of the graph.
            # Nodes/Links outside of this box will be ignored.
            # Should be a tuple (left_lon, top_lat, right_lon, bottom_lat)
    def __init__(
            self,
            nodes_fn,
            links_fn,
            lookup_kd_size=1,
            region_kd_size=1000,
            limit_bbox = None):
        
        if(limit_bbox!=None):
            (left_lon, top_lat, right_lon, bottom_lat) = limit_bbox

        
        
        #Save the filenames for future reference
        self.nodes_fn = nodes_fn
        self.links_fn = links_fn
        
        self.nodes = []  # A list of all Nodes
        self.nodes_by_id = {}  # Maps integer node_ids to Node objects
        self.links = []  # A list of all Links
        # Maps (begin_node_id, end_node_id) to Link objects
        self.links_by_node_id = {}

        self.total_region_count = 0
        
        self.isFlat = False
        self.region_kd_size = region_kd_size
        self.lookup_kd_size = lookup_kd_size

        # Read nodes file and create node objects
        with open(nodes_fn, "r") as f:
            csv_reader = csv.reader(f)
            csv_reader.next()  # throw out header
            for line in csv_reader:
                # Unpack CSV line
                [begin_node_id,
                 is_complete,  # is_complete,
                 _,  # num_in_links,
                 _,  # num_out_links,
                 osm_traffic_controller,  # osm_traffic_controller,
                 longitude,
                 latitude,
                 osm_changeset,  # osm_changeset,
                 birth_timestamp,  # birth_timestamp,
                 death_timestamp,  # death_timestamp,
                 region_id] = line

                
                [latitude, longitude] = map(float, [latitude, longitude])
                
                # Add the node if it is within the bounds of the map
                if(limit_bbox==None or (latitude > bottom_lat and latitude < top_lat and
                    longitude > left_lon and longitude < right_lon)):                
                    
                    self.min_lat = min(self.min_lat, latitude)
                    self.max_lat = max(self.max_lat, latitude)
                    self.min_lon = min(self.min_lon, longitude)
                    self.max_lon = max(self.max_lon, longitude)
                    
                    # build node object
                    node = Node(
                        int(begin_node_id),
                        latitude,
                        longitude,
                        int(region_id))
                        
                    # set additional node properties
                    node.is_complete = bool(is_complete)
                    node.osm_traffic_controller = osm_traffic_controller
                    node.osm_changeset = int(osm_changeset)
                    node.birth_timestamp = int(birth_timestamp)
                    node.death_timestamp = int(death_timestamp)
                    node.region_id = int(region_id)
                    
                    self.nodes.append(node)
                    self.nodes_by_id[node.node_id] = node

        # read Links file and create links
        with open(links_fn, "r") as f:
            csv_reader = csv.reader(f)
            csv_reader.next()  # throw out header
            for line in csv_reader:
                # unpack line
                [_,  # link_id,
                 begin_node_id,
                 end_node_id,
                 begin_angle,  # begin_angle,
                 end_angle,  # end_angle,
                 street_length,
                 osm_name,  # osm_name,
                 osm_class,
                 osm_way_id,  # osm_way_id,
                 _,  # startX,
                 _,  # startY,
                 _,  # endX,
                 _,  # endY,
                 osm_changeset,  # osm_changeset,
                 birth_timestamp,  # birth_timestamp,
                 death_timestamp] = line
                # convert strings to int ids
                 
                [begin_node_id, end_node_id] = map(
                    int, [begin_node_id, end_node_id])

                # If the begin_node and end_node exist, create a Link between
                # them
                if(begin_node_id in self.nodes_by_id and
                   end_node_id in self.nodes_by_id):
                       
                    begin_node = self.nodes_by_id[begin_node_id]
                    end_node = self.nodes_by_id[end_node_id]

                    # Create the Link object and set properties
                    link = Link(begin_node_id, end_node_id,
                                float(street_length))
                    link.origin_node = begin_node
                    link.connecting_node = end_node

                    # Add Link to forward and backward adjacency lists
                    begin_node.forward_links.append(link)
                    end_node.backward_links.append(link)
                    
                    # Save additional link properties
                    link.osm_class = osm_class
                    link.begin_angle = float(begin_angle)
                    link.end_angle = float(end_angle)
                    link.osm_name = osm_name
                    link.osm_class = osm_class
                    link.osm_way_id = int(osm_way_id)
                    link.osm_changeset = int(osm_changeset)
                    link.birth_timestamp = int(birth_timestamp)
                    link.death_timestamp = int(death_timestamp)


                    # Add Link to the list and the lookup table
                    self.links.append(link)
                    self.links_by_node_id[begin_node_id, end_node_id] = link

        for i in xrange(len(self.links)):
            self.links[i].link_id = i


        # Clean the graph by removing extra SCCs
        self.remove_extra_sccs()

        # Build the KD trees
        self.build_kd_trees()


    def delete_nodes(self, bad_nodes):
        # Convert to set for O(1) lookup
        bad_nodes = set(bad_nodes)
        
        # remove these nodes from the graph and the lookup table
        self.nodes = [node for node in self.nodes if node not in bad_nodes]
        for node in bad_nodes:
            _ = self.nodes_by_id.pop(node.node_id)   
            del _
        
        bad_links = set()        
        # remove links connected to these nodes
        for node in bad_nodes:
            for link in node.forward_links:
                link.connecting_node.backward_links.remove(link)
                bad_links.add(link)
            for link in node.backward_links:
                link.origin_node.forward_links.remove(link)
                bad_links.add(link)
        
        # also remove these links from the list and lookup table
        self.links = [link for link in self.links if link not in bad_links]
        for link in bad_links:
            _ = self.links_by_node_id.pop((link.origin_node.node_id, link.connecting_node.node_id))
            del _
        
        # Re-index the link ids, since we have shifted the list around
        for i in xrange(len(self.links)):
            self.links[i].link_id = i
        
        


    # Cleans the graph by forcing it to be one large strongly connected component
    # The largest strongly connected component is extracted from the raw graph,
    # and nodes/links in the remaining SCCs are deleted.
    def remove_extra_sccs(self):
        # find strongly connected components
        sccs = kosaraju(self.nodes)
        
        # determine which scc is largest
        largest_scc = []
        for scc in sccs:
            if(len(scc) > len(largest_scc)):
                largest_scc = scc
                
        # find nodes in other small sccs
        bad_nodes = set()
        for scc in sccs:
            if(scc!=largest_scc):
                bad_nodes.update(scc)
        
        self.delete_nodes(bad_nodes)


    # Builds KD trees to spatially index the nodes of the graph.  This makes
    # geographic queries much faster
    def build_kd_trees(self, split_weights = False):
        # Finally, index nodes using KD Trees
        if split_weights == False:
            self.region_kd_tree = KDTree(self.nodes, leaf_size=self.region_kd_size)
        else:
            self.region_kd_tree = KDTree(self.nodes, leaf_size=self.region_kd_size, split_weights=True)
        self.lookup_kd_tree = KDTree(self.nodes, leaf_size=self.lookup_kd_size)
    
    
    # Matches a list of Trips to their nearest intersections (Nodes) in this Map
    # Upon completion, each trip will have .origin_node and .dest_node attributes
    # For efficiency, duplicates (some orig/dest) are also removed - although the Trips
    # are edited "in place", this function still returns a subset of them.  The trip.dup_times
    # attribute is set, which
    # Params:
        # trips - a list of Trip objects to be map-matched
    def match_trips_to_nodes(self, trips):
        trip_lookup = {} # lookup a trip by origin, destination nodes

        #First find the nearest origin/destination nodes for each trip
        #We will also find duplicate trips (same origin,destination nodes)
        for trip in trips:
            if(trip.isValid() == Trip.VALID):
                trip.num_occurrences = 1
                trip.origin_node = self.get_nearest_node(trip.fromLat, trip.fromLon)
                trip.dest_node = self.get_nearest_node(trip.toLat, trip.toLon)

                if((trip.origin_node, trip.dest_node) in trip_lookup):
                    #Already seen this trip at least once
                    trip_lookup[trip.origin_node, trip.dest_node].num_occurrences += 1
                    trip_lookup[trip.origin_node, trip.dest_node].dup_times.append(trip.time)
                    trip.dup_times = None
                elif trip.origin_node !=None and trip.dest_node != None:
                    #Never seen this trip before
                    trip_lookup[trip.origin_node, trip.dest_node] = trip
                    trip_lookup[trip.origin_node, trip.dest_node].dup_times = [trip.time]
    
        
        #Make unique trips into a list and return
        new_trips = [trip_lookup[key] for key in trip_lookup]
        return new_trips
    
    # Replaces references on Node and Link objects with id numbers.  This way the graph can be pickled
    # and, for example, sent to a worker process
    def flatten(self):
        if(self.isFlat):
            return
        
        self.isFlat = True
        self.region_kd_tree = None
        self.lookup_kd_tree = None
        
        for node in self.nodes:
            if(node.forward_links!= None):
                node.forward_link_ids = [link.link_id for link in node.forward_links]
                node.backward_link_ids = [link.link_id for link in node.backward_links]
                node.forward_links = None
                link.backward_links = None
        
        for link in self.links:
            if(link.origin_node != None):
                link.origin_node_id = link.origin_node.node_id
                link.connecting_node_id = link.connecting_node.node_id
                link.origin_node = None
                link.connecting_node = None
    
    # Reverses the flatten() operation, rebuilding the references between Node and Link objects
    # from id numbers
    def unflatten(self):
        #Ensure that we only have to unflatten the map once
        if(not self.isFlat):
            return
        
        print ("Unflattening map")
            
        self.isFlat = False
        
        for node in self.nodes:
            if(node.forward_link_ids != None):
                node.forward_links = [self.links[_id] for _id in node.forward_link_ids]
                node.backward_links = [self.links[_id] for _id in node.backward_link_ids]
        
        for link in self.links:
            if(link.origin_node_id!=0):
                link.origin_node = self.nodes_by_id[link.origin_node_id]
                link.connecting_node = self.nodes_by_id[link.connecting_node_id]
            
    
        self.build_kd_trees()
    
    def routeTrips(self, trips, num_cpus = 1, max_speed=None, astar_used=False, arcflags_used=False):
        if(max_speed==None):
            max_speed = self.get_max_speed()
        
        if(num_cpus <= 1):
            #Don't use parallel processing - just route all of the trips
            for trip in trips:
                trip.path_links = bidirectional_search(trip.origin_node, trip.dest_node, use_astar=astar_used, use_arcflags=arcflags_used, max_speed=max_speed, curr_map=self)
        else:
            #Use parallel processing - split the trips into chunks
            pass

# A simple test that tries various leaf_sizes for the lookup_kd_tree
# Turns out smaller is always better
def benchmark_node_lookup():
    from datetime import datetime
    print("Loading")
    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    max_speed = nyc_map.get_max_speed()

    print("Max speed = " + str(max_speed))

    print("Reading file")
    sample_trips = []
    with open('sample.csv', 'r') as f:
        r = csv.reader(f)
        r.next()  # throw out header
        for line in r:
            [_,  # medallion,
             _,  # hack_license,
             _,  # vendor_id,
             _,  # rate_code,
             _,  # store_and_fwd_flag,
             _,  # pickup_datetime,
             _,  # dropoff_datetime,
             _,  # passenger_count,
             _,  # trip_time_in_secs,
             _,  # trip_distance,
             pickup_longitude,
             pickup_latitude,
             dropoff_longitude,
             dropoff_latitude] = line

            [pickup_longitude,
             pickup_latitude,
             dropoff_longitude,
             dropoff_latitude] = map(float,
                                     [pickup_longitude,
                                      pickup_latitude,
                                      dropoff_longitude,
                                      dropoff_latitude])
            sample_trips.append(
                [pickup_longitude, pickup_latitude, dropoff_longitude,
                 dropoff_latitude])
            if(len(sample_trips) >= 10000):
                break

    for leaf_size in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50]:
        d1 = datetime.now()
        nyc_map.lookup_kd_tree = KDTree(nyc_map.nodes, leaf_size=leaf_size)
        d2 = datetime.now()
        for [
                pickup_longitude,
                pickup_latitude,
                dropoff_longitude,
                dropoff_latitude] in sample_trips:
            orig = nyc_map.get_nearest_node(pickup_latitude, pickup_longitude)
            # print "calls : " + str(nyc_map.lookup_kd_tree.calls)
            dest = nyc_map.get_nearest_node(
                dropoff_latitude,
                dropoff_longitude)
            # print "calls : " + str(nyc_map.lookup_kd_tree.calls)
        d3 = datetime.now()

        print("leaf_size=" + str(leaf_size) + "   build time: " + str(d2 - d1)
              + "   query time: " + str(d3 - d2))

# Tests the Map.assign_node_regions() method by looking at a few nodes and
# their linked neighbors
# Most of them should have the same region_id


def test_region_ids():
    from random import randint
    print("Loading")
    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")

    print("Assigning node regions")
    nyc_map.assign_node_regions()
    for _ in range(20):
        j = randint(0, len(nyc_map.nodes) - 1)
        node = nyc_map.nodes[j]
        print node.region_id
        for link in node.forward_links:
            print "---" + str(link.connecting_node.region_id)
        for link in node.backward_links:
            print "===" + str(link.origin_node.region_id)
        print

def test_flatten():
    print("Loading")
    d1 = datetime.now()
    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv")
    d2 = datetime.now()
    print(d2 - d1)
    print("Flattening")
    nyc_map.flatten()
    d3 = datetime.now()
    print(d3 - d2)
    print("Unflattening")
    nyc_map.unflatten()
    d4 = datetime.now()
    print(d4 - d3)

# memory usage of this process in MB
def getmem():
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1000.0

def test_memory_usage():
    from db_functions import db_main, db_trip
    from datetime import datetime
    print("Before: %f" % getmem())
    nyc_map = Map("nyc_map4/nodes.csv", "nyc_map4/links.csv", limit_bbox=Map.reasonable_nyc_bbox)
    print [nyc_map.min_lat, nyc_map.max_lat, nyc_map.min_lon, nyc_map.max_lon]
    
    db_main.connect('db_functions/database.conf')
    d1 = datetime(2012,1,10,9)
    d2 = datetime(2012,1,10,10)
    trips = db_trip.find_pickup_dt(d1, d2)
    print("Matching...")
    nyc_map.match_trips_to_nodes(trips)
    

    print("After : %f" % getmem())
    del(nyc_map)

    

if(__name__ == "__main__"):
    # benchmark_node_lookup()
    #test_region_ids()
    test_memory_usage()
