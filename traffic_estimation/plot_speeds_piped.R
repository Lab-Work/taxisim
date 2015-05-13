#library(RgoogleMaps)
clat = 40.773455
clon = -73.962880
z = 12

lat_meters = 111194.86461
lon_meters = 84253.1418965



#jet.colors =colorRamp(c("#00007F", "blue", "#007FFF", "cyan",
#                     "#7FFF7F", "yellow", "#FF7F00", "red"))

jet.colors =colorRamp(c("blue", "#007FFF", "cyan",
                     "#7FFF7F", "yellow", "#FF7F00", "red"))




linearScale = function(x, lo, hi){
	x = (x - lo) / (hi - lo)
	return(pmax(pmin(x, 1), 0))
}



argv = commandArgs(trailingOnly=T)



outfile = argv[1]
my_title = argv[2]
plot_type = argv[3]
print(plot_type)

if(plot_type=="absolute"){
	print("ASDFASF")
	lo_pace = 1
	hi_pace = 15
	value_granularity=10
	legend_granularity=1
} else if(plot_type=="zscore"){
	lo_pace=-5
	hi_pace=5
	value_granularity=30
	legend_granularity=1
}

#print(my_title)

#infile = paste("iteration_", i, ".csv", sep="")
#outfile = paste("map_",i,".pdf", sep="")


#print(paste("Reading", infile))

png(outfile, 1024, 1024)
par(mar=c(0,2,4,2), family="sans")
layout(c(1,2), heights=c(7,1))


t = read.csv('stdin')


t$start_lat = t$start_lat * lat_meters
t$end_lat = t$end_lat * lat_meters
t$start_lon = t$start_lon * lon_meters
t$end_lon = t$end_lon * lon_meters






#print("Computing colors")
#summary(t$speed)
t$pace[is.na(t$pace)] = 0

#convert the pace to minutes per mile
t$pace = t$pace * 26.8224

cvals = linearScale(t$pace, lo_pace, hi_pace)
cols = rgb(jet.colors(cvals)/255)
#cols=rgb(jet.colors(t$speed/31)/255)

#cols = rgb(jet.colors(log(t$speed+1)/3.44)/255)

#mymap = GetMap(center=c(clat, clon), zoom=z)
#print("Plotting")
#PlotOnStaticMap(mymap, clat, clon, col="black", pch=15, cex=400)
#PlotArrowsOnStaticMap(mymap, lat0=t$start_lat, lon0=t$start_lon, lat1=t$end_lat, lon1=t$end_lon, FUN=segments, add=T, col=cols,lwd=3)

size = 8000
plot(clon,clat,type="n",
	xlim=c(clon*lon_meters-size,clon*lon_meters+size),
	ylim=c(clat*lat_meters-size, clat*lat_meters+size),
	xaxt="n", yaxt="n", xlab="", ylab="")
abline(v = clon*lon_meters, col = "black", lwd = 2000)


segments(t$start_lon, t$start_lat, x1=t$end_lon, y1=t$end_lat, col=cols, lwd=1)
#arrows(t$start_lon, t$start_lat, x1=t$end_lon, y1=t$end_lat, col=cols, lwd=1, angle=15, length=.1)






par(mar=c(0,1,3,1))
title(main=my_title, cex.main=3)


print("Adding legend")
plot(0,0, type="n", xlim=c(lo_pace,hi_pace), ylim=c(0,1), xaxt="n", yaxt="n", , bty="n", cex.main=.8, main="")


	
	vals = seq(lo_pace, hi_pace, 1/value_granularity)
	cvals = linearScale(vals, lo_pace, hi_pace)
	mycols = rgb(jet.colors(cvals)/255)
	a = c((0:((hi_pace - lo_pace)/legend_granularity))*value_granularity*legend_granularity + 1)



        yvals = rep(.6,length(vals))
	points(vals, yvals, col=mycols, pch=15, cex=2)
	
	
	print(a)
	print(vals[a])
	print(vals[a])
	#axis(1, at=a, labels=round(vals[a], 2))
	#abline(v=a)
	if(plot_type=="absolute"){
		units = "Pace (min/mi)"
	} else if(plot_type=="zscore"){
		units = "Pace Z-Score"
	}
	text(x=(hi_pace+lo_pace)/2,y=.9,labels=units, cex=2, col.main="white")
	segments(x0=vals[a],y0=.4,x1=vals[a],y1=.6, lwd=1)
	#arrows(x0=vals[a],y0=.4,x1=vals[a],y1=.6, lwd=1, angle=15, length=.1)
	text(x=vals[a],y=.2,labels=vals[a], cex=2, )

dev.off()

