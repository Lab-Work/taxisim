# A class that represents the links in the map that connect two nodes together
import numpy as np
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
        self.road_class = ""

        self.forward_arc_flags_vector = None
        self.backward_arc_flags_vector = None
    
    def get_forward_arcflags_hex(self):
        return self.arcflags_to_hex(self.forward_arc_flags_vector)
        
    def get_backward_arcflags_hex(self):
        return self.arcflags_to_hex(self.backward_arc_flags_vector)

    def arcflags_to_hex(self, direction):
        hexString = []
        curr_val = [8,4,2,1]
        hex_val = 0
        for i in range(len(direction)):
            hex_val += int(direction[i])*curr_val[i%4]
            if i%4 == 3 or i==len(direction)-1:
                hexString.append(hex(hex_val)[2:3])
                hex_val = 0
        return ''.join(hexString)    

    def decode_forward_arcflags_hex(self, hex_string, region_count):
        self.decode_flags(hex_string, self.forward_arc_flags_vector, region_count)

    def decode_backward_arcflags_hex(self, hex_string, region_count):
        self.decode_flags(hex_string, self.backward_arc_flags_vector, region_count)

    def decode_flags(self, hex_string, direction, region_count):
        if direction == None:
            direction = np.empty(hex_string*4, dtype=bool)
        bin_string = bin(int(hex_string, 16))[2:]
        initial = region_count-len(bin_string)
        for i in range(initial, region_count):
            if bin_string[i-initial] == "1":
                direction[i] = True
        direction = direction[0:region_count]



    # def decode_flags(self, hex_string, direction, region_count):
    #     if direction == None:
    #         direction = np.empty(hex_string*4, dtype=bool)
    #     bin_string = bin(int(hex_string, 16))[2:]
    #     start = 0
    #     if len(bin_string) < region_count:
    #         start = region_count-len(bin_string)
    #     if len(bin_string) > region_count:
    #         bin_string = bin_string[:region_count]

    #     for i in range(start, len(bin_string)):
    #         if bin_string[i] == "1":
    #             direction[i] = True




