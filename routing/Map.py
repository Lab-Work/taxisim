from KDTree import KDTree
import csv
from Node import Node
from Link import Link
from traffic_estimation.Trip import Trip
from BiDirectionalSearch import bidirectional_search
from datetime import datetime

# Represents a roadmap, has a set of Nodes and Links


class Map:
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
                if connecting_node.region != node.region:
                    connecting_node.is_boundary_node = True

        print "total regions : " + str(next_region_id)

    # Finds the maximum speed of any link in the graph
    def get_max_speed(self):
        max_speed = 0.0
        for link in self.links:
            if(link != self.idle_link):
                link_speed = float(link.length) / link.time
                max_speed = max(max_speed, link_speed)
        return max_speed
    
    def get_default_speed(self):
        for link in self.links:
            if(link != self.idle_link and link.num_trips==0):
                link_speed = float(link.length) / link.time
                return link_speed
        return None

    def set_all_link_speeds(self, speed):
        for link in self.links:
            link.time = link.length / speed

    def save_speeds(self, filename):
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['start_node_id',
                             'end_node_id',
                             'start_lat',
                             'start_lon',
                             'end_lat',
                             'end_lon',
                             'speed'])
            for link in self.links:
                speed = link.length / link.time
                writer.writerow([link.origin_node.node_id,
                                 link.connecting_node.node_id,
                                 link.origin_node.lat,
                                 link.origin_node.long,
                                 link.connecting_node.lat,
                                 link.connecting_node.long,
                                 speed])

    # Builds the Map from CSV files describing the Nodes and LInks
    # Params:
        # nodes_fn - the name of the CSV file containing Node info
        # links_fn - the name of the CSV file containing Link info
        # lookup_id_size - the leaf_size for the Node lookup kd tree.  Should
        # be small for fastest performance
        # region_id_size - the leaf_size for the region kd tree.  Should be
        # large
    def __init__(
            self,
            nodes_fn,
            links_fn,
            lookup_kd_size=1,
            region_kd_size=1000):
        
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

        # Read nodes file and create node objects
        with open(nodes_fn, "r") as f:
            csv_reader = csv.reader(f)
            csv_reader.next()  # throw out header
            for line in csv_reader:
                # Unpack CSV line
                [begin_node_id,
                 _,  # is_complete,
                 _,  # num_in_links,
                 _,  # num_out_links,
                 _,  # osm_traffic_controller,
                 longitude,
                 latitude,
                 _,  # osm_changeset,
                 _,  # birth_timestamp,
                 _,  # death_timestamp,
                 region_id] = line

                # grow the bounds of the map if necessary
                [latitude, longitude] = map(float, [latitude, longitude])
                self.min_lat = min(self.min_lat, latitude)
                self.max_lat = max(self.max_lat, latitude)
                self.min_lon = min(self.min_lon, longitude)
                self.max_lon = max(self.min_lon, longitude)

                node = Node(
                    int(begin_node_id),
                    latitude,
                    longitude,
                    int(region_id))
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
                 _,  # begin_angle,
                 _,  # end_angle,
                 street_length,
                 _,  # osm_name,
                 _,  # osm_class,
                 _,  # osm_way_id,
                 _,  # startX,
                 _,  # startY,
                 _,  # endX,
                 _,  # endY,
                 _,  # osm_changeset,
                 _,  # birth_timestamp,
                 _,  # death_timestamp
                 ] = line
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

                    # Add Link to the list and the lookup table
                    self.links.append(link)
                    self.links_by_node_id[begin_node_id, end_node_id] = link

        for i in xrange(len(self.links)):
            self.links[i].link_id = i

        # Create the "idle link", which represents waiting
        self.idle_link = Link(0,0,0)
        self.idle_link.time = 300 # Default waiting time of 5 minutes
        self.idle_link.link_id = i + 1
        self.links.append(self.idle_link)


        # Finally, index nodes using KD Trees
        self.region_kd_tree = KDTree(self.nodes, leaf_size=region_kd_size)
        self.lookup_kd_tree = KDTree(self.nodes, leaf_size=lookup_kd_size)
    
    
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
            
    
    
    def routeTrips(self, trips, num_cpus = 1, max_speed=None):
        if(max_speed==None):
            max_speed = self.get_max_speed()
        
        if(num_cpus <= 1):
            #Don't use parallel processing - just route all of the trips
            for trip in trips:
                trip.path_links = bidirectional_search(trip.origin_node, trip.dest_node, use_astar=True, max_speed=max_speed)
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
    

if(__name__ == "__main__"):
    # benchmark_node_lookup()
    #test_region_ids()
    test_flatten()