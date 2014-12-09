# A class that represents the links in the map that connect two nodes together
class Link:
    def __init__(self, node_id, length, speed=10):
        self.origin_node_id = node_id
        self.length = float(length)
        self.time = float(length) / float(speed)
        self.origin_node = None
        self.connecting_node = None
