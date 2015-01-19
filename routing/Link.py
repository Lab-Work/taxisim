# A class that represents the links in the map that connect two nodes together
class Link:
    def __init__(self, begin_node_id, end_node_id, length, speed=10):
        self.origin_node_id = int(begin_node_id)
        self.connecting_node_id = int(end_node_id)
        self.length = float(length)
        self.time = float(length) / float(speed)
        self.origin_node = None
        self.connecting_node = None
        
        self.link_id = 0
        self.num_trips = 0
