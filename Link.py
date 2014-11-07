class Link:
    def __init__(self, node_id, weight, speed, time):
        self.origin_node_id = node_id
        self.weight = float(weight)
        self.speed = float(speed)
        self.time = float(weight) / float(speed)
        self.connecting_node = None

    def add_connecting_node(self, connecting_node):
        self.connecting_node = connecting_node
