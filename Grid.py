class grid_region:

    # A square region with latitude and longitude coordinates bounding it
    # as well as every Node within it.
    def __init__(self, up_bound, low_bound, right_bound, left_bound):
        self.up = up_bound
        self.down = low_bound
        self.left = left_bound
        self.right = right_bound
        self.nodes = set()


# Given an overall area and how many regions you want
# (num_divisions x num_divisions)
# return a list of grid_regions that make up the overall map and put all the
# nodes necessary in each grid_region from list_of_nodes
def set_up_grid(upmost, downmost, rightmost, leftmost, num_divisions, nodes):
    grid = []
    # The height and width of each grid region
    change_in_lat = (upmost - downmost)/float(num_divisions)
    change_in_long = (rightmost - leftmost)/float(num_divisions)
    curr_left = leftmost
    # Left-Right
    for i in range(num_divisions):
        # Each subList represents  a bunch of grid regions within some
        # longitude constraint
        curr_down = downmost
        thisLong = []
        for j in range(num_divisions):
            # We are creating a new grid_region
            newRegion = grid_region(
                curr_down + change_in_lat, curr_down,
                curr_left + change_in_long, curr_left)
            thisLong.append(newRegion)
            curr_down += change_in_lat
        grid.append(thisLong)
        curr_left += change_in_long
    for Node in nodes:
        # The coordinates hashed into the grid based off the Node's latitude
        # and longitude
        i = int(float(Node.long - leftmost) / float(change_in_long))
        j = int(float(Node.lat - downmost) / float(change_in_lat))
        grid[i][j].nodes.add(Node)
    return grid
