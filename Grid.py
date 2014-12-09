class GridRegion:

    # A square region with latitude and longitude coordinates bounding it
    # as well as every Node within it.
    def __init__(self, up_bound, low_bound, right_bound, left_bound):
        self.up = up_bound
        self.down = low_bound
        self.left = left_bound
        self.right = right_bound
        self.nodes = set()

    # Gets all of the boundary nodes in this region
    def get_boundary_nodes(self):
        boundary_nodes = []
        for node in self.nodes:
            if node.is_boundary_node:
                boundary_nodes.append(node)
        return boundary_nodes


# Given an overall area and how many regions you want
# (num_divisions x num_divisions)
# return a list of GridRegions that make up the overall map and put all the
# nodes necessary in each GridRegion from list_of_nodes
def set_up_grid(upmost, downmost, rightmost, leftmost, num_divisions, nodes):
    grid = []
    # The height and width of each grid region
    change_in_lat = (upmost - downmost) / float(num_divisions)
    change_in_long = (rightmost - leftmost) / float(num_divisions)
    curr_left = leftmost
    # Left-Right
    for i in range(num_divisions):
        # Each subList represents  a bunch of grid regions within some
        # longitude constraint
        curr_down = downmost
        thisLong = []
        for j in range(num_divisions):
            # We are creating a new GridRegion
            newRegion = GridRegion(
                curr_down + change_in_lat, curr_down,
                curr_left + change_in_long, curr_left)
            thisLong.append(newRegion)
            curr_down += change_in_lat
        grid.append(thisLong)
        curr_left += change_in_long
    for node in nodes:
        # The coordinates hashed into the grid based off the Node's latitude
        # and longitude
        i = int(float(node.long - leftmost) / float(change_in_long))
        j = int(float(node.lat - downmost) / float(change_in_lat))
        grid[i][j].nodes.add(node)

        # Also store the region mapping on the node object
        node.region_id = (i, j)

    return grid
