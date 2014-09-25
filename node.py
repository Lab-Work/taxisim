import csv
from grid import setUpGrid

#TODO: REMOVE THE DUPLICATE STUFF TAKING INTO ACCOUNT NONES


#A vertex in our map (edge class not used -> simply used lists within the node)
class Node:

    def __init__(self, _id, latitude, longitude, region):
        self.id = _id
        self.lat = float(latitude)
        self.long = float(longitude)
        self.region = int(region)

        # Used during the route calculator
        #   -> this keeps track of the node previous to this one in a path
        # i.e. If the path was A->C->B->D, B.cameFrom == C
        self.came_from = None

        # Used for DFS
        self.discovered = False

        # Keeps track of how far away we are from the startNode
        self.best_time = float("INF")

        # These are nodes that are connected by edges that start at the current node and their
        # weights
        self.distance_connections = {}
        self.backwards_connections = {}  # Measured in meters
        self.speed_connections = {}
        self.time_connections = {}
        self.is_arc_flags = {}
        self.is_backwards_arc_flags = {}

        ######################################################
        #  Used in multiple dijkstra arcflag precomputation  #
        ######################################################

        # Tells if the node is a boundary node
        self.is_boundary_node = False

        # During the dijkstra algorithm, give a set of which indices were updated
        self.wasUpdated = set()

        self.timeFromBoundaryNode = []

        # For each boundary node path, shows where this particular node came from
        self.arcFlagPaths = []

        # Checks if the node is currently in the queue (won't add otherwise)
        self.inQueue = False

    # Given an ID, gives its weight
    def add_connecting_node(self, _id, weight, speed, time):
        self.distance_connections[_id] = float(weight)
        self.speed_connections[_id] = float(speed)
        self.time_connections[_id] = float(weight)/float(speed)

    def set_arc_flags(self, _id, hex_string):
        new_list = hex_decrypter(hex_string)
        self.is_arc_flags[_id] = new_list

    def add_backwards_node(self, _id, weight):
        self.backwards_connections[_id] = float(weight)

    # Sets all of the streets to that initial speed
    def set_speed_connections(self, init_speed):
        for connection in self.distance_connections:
            self.speed_connections[connection] = init_speed
            self.time_connections[connection] = self.distance_connections[connection] / init_speed

    def find_min_boundary_time(self):
        return min(self.timeFromBoundaryNode)


# For converting the regions in the arcFlags csv file back into binary from hex
def hex_decrypter(hex_string):
    new_string = bin(int(hex_string, 16))[2:]
    new_list = map(int, list(new_string))
    if len(new_list) < 400:
        new_list = [0] * (400 - len(new_list)) + new_list
    return new_list


##############################
#        NON ARC FLAG        #
##############################

# Instead of them distance_connections using ID's as the keys, they use actual Nodes.
# Also sets up boundary nodes and arcflags
def fix_nodes(dict_of_nodes, has_speeds, has_arc_flags):
    for ID in dict_of_nodes:
        curr_node = dict_of_nodes[ID]
        new_connections = {}
        speed_connections = {}
        time_connections = {}
        arc_flags = {}

        for connectingNodeID in curr_node.distance_connections:
            try:
                new_node = dict_of_nodes[connectingNodeID]
                if new_node != -1:
                    # The new way is pass in a node, instead of the ID
                    new_connections[new_node] = curr_node.distance_connections[connectingNodeID]
                    speed_connections[new_node] = curr_node.speed_connections[connectingNodeID]
                    time_connections[new_node] = curr_node.time_connections[connectingNodeID]

                    # Set is_arc_flags[new_node] = secondDict{}
                    # secondDict[RegionNumber] = True or False
                    if has_arc_flags is None:
                        curr_node.is_arc_flags[new_node] = False
                    else:
                        arc_flags[new_node] = curr_node.is_arc_flags[connectingNodeID]
            except KeyError:
                pass
        curr_node.distance_connections = new_connections
        curr_node.speed_connections = speed_connections
        curr_node.time_connections = time_connections
        if has_arc_flags is not None:
            curr_node.is_arc_flags = arc_flags

    for node_id in dict_of_nodes:
        node = dict_of_nodes[node_id]
        for connectingNode in node.time_connections:
            connectingNode.backwards_connections[node] = node.time_connections[connectingNode]
            if connectingNode.region != node.region:
                connectingNode.isBoundaryNode = True


# Returns a set of nodes with all their distance_connections properly set
def set_up_nodes(time_file, arc_flag_file):
    dict_of_links = dict()
    all_links = csv.reader(open("nyc_map4/links.csv", 'rb'), delimiter=',')
    speed_of_links = None
    if time_file is not None:
        speed_of_links = csv.reader(open(time_file, 'rb'), delimiter=',')
    arc_flags = None
    if arc_flag_file is not None:
        arc_flags = csv.reader(open(arc_flag_file, 'rb'), delimiter=',')
    # Dictionary should be startNodeID -> setOfAllLinks that have that startNode
    header = True
    for link in all_links:
        if header:
            header = False
            continue
        if link[1] in dict_of_links:
            dict_of_links[link[1]].append(link)
        else:
            dict_of_links[link[1]] = []
            dict_of_links[link[1]].append(link)
    # Key is startNode, list of all streets that start at that node
    header = True
    # Key is startNode, adds speeds of links
    if speed_of_links is not None:
        for link in speed_of_links:
            if header:
                header = False
                continue
            curr_list = dict_of_links[link[0]]
            for origLink in curr_list:
                #If the endNodes are the same (streets are the same)
                if origLink[2] == link[1]:
                    origLink.append(link[3])  # Speed of link
                    origLink.append(link[4])  # Time of link
    header = True
    # Key is startNode, adds arcLinks
    if arc_flags is not None:
        for link in arc_flags:
            if header:
                header = False
                continue
            curr_list = dict_of_links[link[0]]
            for origLink in curr_list:
                # If the endNodes are the same (streets are the same)
                if origLink[2] == link[1]:
                    origLink.append(link[2])
    dict_of_nodes = dict()
    all_nodes = csv.reader(open("nyc_map4/nodes.csv", 'rb'), delimiter=',')
    counter = 0
    for aNode in all_nodes:
        # Want to ignore the header line
        if counter != 0:
            # Creates the nodes and put them in the dictionary, with the ID as the key
            new_node = Node(aNode[0], aNode[6], aNode[5], aNode[10])
            try:
                list_of_links = dict_of_links[new_node.id]
                for link in list_of_links:
                    if link[2] != new_node.id and len(link) == 19 and float(link[17]) > 0:
                        new_node.add_connecting_node(link[2], link[5], link[16], link[17])
                        new_node.set_arc_flags(link[2], link[18])
                    if link[2] != new_node.id and len(link) == 18 and float(link[17]) > 0:
                        new_node.add_connecting_node(link[2], link[5], link[16], link[17])
                    if link[2] != new_node.id and len(link) == 16:
                        new_node.add_connecting_node(link[2], link[5], 5, float(link[5])/5)
            except KeyError:
                pass
            dict_of_nodes[new_node.id] = new_node
        counter += 1
    # Changes what they connections keys are (from node ID's to nodes)
    fix_nodes(dict_of_nodes, speed_of_links, arc_flags)
    set_of_nodes = set()
    for ID in dict_of_nodes:
        set_of_nodes.add(dict_of_nodes[ID])
    return set_of_nodes


# Returns an array that goes like this
# [MaxLat, MinLat, MaxLong, MinLong]
def get_node_info(arr):
    node_info = [-1000, 1000, -1000, 1000]
    for node in arr:
        if float(node.lat) > node_info[0]:
            node_info[0] = float(node.lat)
        if float(node.lat) < node_info[1]:
            node_info[1] = float(node.lat)
        if float(node.long) > node_info[2]:
            node_info[2] = float(node.long)
        if float(node.long) < node_info[3]:
            node_info[3] = float(node.long)
    return node_info


# If no arcFlags, arcFlagFile == None
def get_correct_nodes(num_divisions, time_file, arc_flag_file):
    nodes = set_up_nodes(time_file, arc_flag_file)
    if time_file is None:
        for node in nodes:
            for connection in node.speed_connections:
                node.speedConnection[connection] = 5
                node.timeConnection[connection] = node.distanceConnection[connection]/5
    node_info = get_node_info(nodes)
    return setUpGrid(node_info[0] + .01, node_info[1], node_info[2] + .01, node_info[3],
                     num_divisions, nodes)


# Returns an array that goes like this
# [MaxLat, MinLat, MaxLong, MinLong]
def get_node_range(grid_of_nodes):
    node_info = [-1000, 1000, -1000, 1000]
    for column in grid_of_nodes:
        for region in column:
            for node in region.nodes:
                if float(node.lat) > node_info[0]:
                    node_info[0] = float(node.lat)
                if float(node.lat) < node_info[1]:
                    node_info[1] = float(node.lat)
                if float(node.long) > node_info[2]:
                    node_info[2] = float(node.long)
                if float(node.long) < node_info[3]:
                    node_info[3] = float(node.long)
    node_info[0] += .01
    node_info[2] += .01
    return node_info

if __name__ == "__main__":
    print "Running"
    ## get_correct_nodes_arcs(20, "speeds_per_hour/0_0" ,"arcFlags/20Regions0_0.csv")
