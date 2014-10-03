# WHAT AN ARRAYFROMCSV CONSISTS OF:
# medallion,tripSeconds,trip_distance,pickup_longitude,pickup_latitude,dropoff_longitude,dropoff_latitude,start_nodeID,end_nodeID


class Trip:
    def __init__(self, csv_arr):
        self.medallion = csv_arr[0]
        self.trip_time = float(csv_arr[1])
        self.trip_dist = float(csv_arr[2])
        self.start_long = float(csv_arr[3])
        self.start_lat = float(csv_arr[4])
        self.end_long = float(csv_arr[5])
        self.end_lat = float(csv_arr[6])
        self.start_node = float(csv_arr[7])
        self.end_node = float(csv_arr[8])

        # The number of trips that this Trip used to be before it was condensed
        self.numTrips = float(csv_arr[9])

        # The list of nodes traversed in order
        # between the start_node and end_node
        self.nodeList = []

        # A dictionary that, given the street ID (start_node.id, end_node.id)
        # will return the two nodes (start_node, end_node)
        self.node_dict = dict()

        # How long the Trip is estimated last
        self.est_time = 0
