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

        self.forward_arc_flags_vector = None
        self.backward_arc_flags_vector = None
    
    def get_forward_arcflags_hex(self):
        hexString = []
        for i in xrange(0,len(self.forward_arc_flags_vector), 4):
            hex_val = int(self.forward_arc_flags_vector[i])*8 + int(self.forward_arc_flags_vector[i+1])*4 + int(self.forward_arc_flags_vector[i+2])*2 + int(self.forward_arc_flags_vector[i+3])
            hexString.append(hex(hex_val)[2:3])
        if i < len(self.forward_arc_flags_vector):
        	i+=1
        	hex_val += (int)(self.forward_arc_flags_vector[i])*8
        	i+=1
	        if i < len(self.forward_arc_flags_vector):
	        	hex_val += (int)(self.forward_arc_flags_vector[i])*4
	       	i+=1
	        if i < len(self.forward_arc_flags_vector):
	        	hex_val += (int)(self.forward_arc_flags_vector[i])*2
        	hexString.append(hex(hex_val)[2:3])
        return ''.join(hexString)
        
    def get_backward_arcflags_hex(self):
        hexString = []
        for i in xrange(0,len(self.backward_arc_flags_vector), 4):
            hex_val = int(self.backward_arc_flags_vector[i])*8 + int(self.backward_arc_flags_vector[i+1])*4 + int(self.backward_arc_flags_vector[i+2])*2 + int(self.backward_arc_flags_vector[i+3])
            hexString.append(hex(hex_val)[2:3])
        if i < len(self.backward_arc_flags_vector):
        	i+=1
        	hex_val += (int)(self.backward_arc_flags_vector[i])*8
        	i+=1
	        if i < len(self.backward_arc_flags_vector):
	        	hex_val += (int)(self.backward_arc_flags_vector[i])*4
	        i+=1
	        if i < len(self.backward_arc_flags_vector):
	        	hex_val += (int)(self.backward_arc_flags_vector[i])*2
        	hexString.append(hex(hex_val)[2:3])
        return ''.join(hexString)

    def decode_forward_arcflags_hex(self, hex_string):
        if self.forward_arc_flags_vector == None:
            self.forward_arc_flags_vector = np.empty(4*len(hex_string), dtype=bool)
        count = 0
        for i in range(len(hex_string)):
            curr_hex = int(hex_string[i],16)
            self.forward_arc_flags_vector[count] = (bool(curr_hex/8))
            if curr_hex - 8 >= 0:
                curr_hex = curr_hex-8
            count+=1
            self.forward_arc_flags_vector[count] = (bool(curr_hex/4))
            if curr_hex - 4 > 0:
                curr_hex = curr_hex-4
            count+=1
            self.forward_arc_flags_vector[count] = (bool(curr_hex/2))
            if curr_hex - 2 > 0:
                curr_hex = curr_hex-2
            count+=1
            self.forward_arc_flags_vector[count] = (bool(curr_hex))
            count+=1


    def decode_backward_arcflags_hex(self, hex_string):
        if self.backward_arc_flags_vector == None:
            self.backward_arc_flags_vector = np.empty(4*len(hex_string), dtype=bool)
        count = 0
        for i in range(len(hex_string)):
            curr_hex = int(hex_string[i],16)
            self.backward_arc_flags_vector[count] = (bool(curr_hex/8))
            if curr_hex - 8 >= 0:
                curr_hex = curr_hex-8
            count+=1
            self.backward_arc_flags_vector[count] = (bool(curr_hex/4))
            if curr_hex - 4 > 0:
                curr_hex = curr_hex-4
            count+=1
            self.backward_arc_flags_vector[count] = (bool(curr_hex/2))
            if curr_hex - 2 > 0:
                curr_hex = curr_hex-2
            count+=1
            self.backward_arc_flags_vector[count] = (bool(curr_hex))
            count+=1



