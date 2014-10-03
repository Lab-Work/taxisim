import csv

from Node import get_correct_nodes

# This entire thing is an implementation of Kosaraju's Algorithm for finding
# strongly connected components. If there are weakly connected components we
# would like to rid ourselves of them
# http://en.wikipedia.org/wiki/Kosaraju%27s_algorithm


# A Stack object
class Stack:

    def __init__(self):
        self.s = []
        self.set = set()
        self.latest_element_index = -1

    def push(self, obj):
        self.latest_element_index += 1
        self.set.add(obj)
        if len(self.s) == self.latest_element_index:
            self.s.append(obj)
        else:
            self.s[self.latest_element_index] = obj

    def last_elem(self):
        return self.s[self.latest_element_index]

    def pop(self):
        obj = self.s[self.latest_element_index]
        self.s[self.latest_element_index] = -1
        self.latest_element_index -= 1
        self.set.discard(obj)
        return obj

    def exists_in(self, obj):
        return (obj in self.set)

    def size(self):
        return self.latest_element_index + 1

    def reset_nodes(self):
        for node in self.s:
            node.discovered = False


def get_first_false(grid_of_nodes):
    for column in grid_of_nodes:
        for region in column:
            for node in region.nodes:
                if node.discovered is False:
                    return node
    return None


# An implementation of dfs, whether on the transpose graph or the actual graph
def dfs(node, stack, transpose):
    node.discovered = True
    temp_stack = Stack()
    temp_stack.push(node)
    if transpose is False:
        while temp_stack.size() != 0:
            curr_node = temp_stack.last_elem()
            for connection in curr_node.distance_connections:
                if connection.discovered is False:
                    connection.discovered = True
                    temp_stack.push(connection)
            if curr_node == temp_stack.last_elem():
                stack.push(temp_stack.pop())
    else:
        while temp_stack.size() != 0:
            curr_node = temp_stack.last_elem()
            for connection in curr_node.backwards_connections:
                if connection.discovered is False:
                    connection.discovered = True
                    temp_stack.push(connection)
            if curr_node == temp_stack.last_elem():
                stack.push(temp_stack.pop())


def reset_nodes(grid_of_nodes):
    for column in grid_of_nodes:
        for region in column:
            for node in region.nodes:
                node.discovered = False

new_file = open("Blacklist.csv", 'wb')
new_file_writer = csv.writer(new_file)
headers = ["SubgraphNumber", "Type", "nodeID", "FromLong", "FromLat",
           "ToLong", "ToLat", "Color"]
new_file_writer.writerow(headers)

# All nodes in NYC
grid_of_nodes = get_correct_nodes(20, "speeds_per_hour/0_0", None)
stack_of_nodes = Stack()
node = get_first_false(grid_of_nodes)

# This is a depth first search upon the graph -> The moment one node terminates
# it is added to the Stack. If component terminates, it will continue on to the
# next component until all components terminate.
while node is not None:
    dfs(node, stack_of_nodes, False)
    node = get_first_false(grid_of_nodes)

# We set every node to undiscovered again
stack_of_nodes.resetnodes()
reset_nodes(grid_of_nodes)
sub_graph_number = 0

# The latter part of of Kosaraju's algorithm. We perform a dfs upon each object
# starting at the top of the Stack. Once that particular dfs terminates, we
# know that is a strongly connected component and write it to the CSV file (all
# under the same subgraph number).
while stack_of_nodes.size() != 0:
    curr_node = stack_of_nodes.pop()
    if curr_node.discovered is True:
        continue
    dfs_stack = Stack()
    dfs(curr_node, dfs_stack, True)

    # We assume for New York City that most components are connected (More
    # than 90%). Thus, for our ~ 100000 nodes, all non strongly connected
    # components will be of size < 10000
    if dfs_stack.size() < 10000:
        while dfs_stack.size() != 0:
            node = dfs_stack.pop()
            new_arr = [sub_graph_number, "node", node.id, node.long, node.lat,
                       0, 0, "red"]
            new_file_writer.writerow(new_arr)
            for connection in node.distance_connections:
                new_arr = [sub_graph_number, "link", node.id, node.long,
                           node.lat, connection.long, connection.lat, "black"]
                new_file_writer.writerow(new_arr)
    sub_graph_number += 1
