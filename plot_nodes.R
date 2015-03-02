# Read the nodes table from the csv file
nodes_table = read.csv("nyc_map4/nodes.csv")

# Create a PNG file to draw
png("NodesMap.png", 1024, 1024)

# Make a scatterplot of nodes (x=lon, y=lat)
# pch - change the shape of the points
# cex - change the size of the points
plot(nodes_table$xcoord, nodes_table$ycoord, col="blue", pch=15, cex=.3, xlab="Longitude", ylab="Latitude")

# Close the PNG file
dev.off()
