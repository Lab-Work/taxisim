# Read the nodes table from the csv file
n = read.csv("../nyc_map4/region.csv")

# Create a PNG file to draw
png("../NodesRegionMap.png", 1024, 1024)

# Make a scatterplot of nodes (x=lon, y=lat)
# pch - change the shape of the points
# cex - change the size of the points

rbPal <- colorRampPalette(c('red', 'orange', 'yellow', 'green', 'blue', 'purple', 'violet', 'black'))
n$col <- rbPal(128)[as.numeric(cut(n$color_id, breaks = 128))]

plot(n$long, n$lat, col=n$col, pch=15, cex=.3, xlab="Longitude", ylab="Latitude")

# Close the PNG file
dev.off()
