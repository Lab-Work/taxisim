# A class that represents the links in the map that connect two nodes together
class Link:
    def __init__(self, node_id, weight, speed, time):
        self.origin_node_id = node_id
        self.weight = float(weight)
        self.speed = float(speed)
        self.time = float(weight) / float(speed)
        self.connecting_node = None
