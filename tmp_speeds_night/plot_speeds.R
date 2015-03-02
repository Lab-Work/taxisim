library(RgoogleMaps)
clat = 40.773455
clon = -73.952880
z = 12
print("Reading")
jet.colors =colorRamp(c("#00007F", "blue", "#007FFF", "cyan",
                     "#7FFF7F", "yellow", "#FF7F00", "red", "#7F0000"))

for(i in 0:10){

infile = paste("iteration_", i, ".csv", sep="")
outfile = paste("map_",i,".png")


png(outfile, 1280, 1280)
t = read.csv(infile)
print("Computing colors")
summary(t$speed)
t$speed[is.na(t$speed)] = 0
cols=rgb(jet.colors(t$speed/31)/255)
mymap = GetMap(center=c(clat, clon), zoom=z)
print("Plotting")
PlotOnStaticMap(mymap, clat, clon, col="black", pch=15, cex=400)
PlotArrowsOnStaticMap(mymap, lat0=t$start_lat, lon0=t$start_lon, lat1=t$end_lat, lon1=t$end_lon, FUN=segments, add=T, col=cols)
dev.off()

}

