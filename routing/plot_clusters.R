argv = commandArgs(trailingOnly=T)
print(argv)
input_filename = argv[1]
link_filename = argv[2]
output_filename = argv[3]


if(link_filename=='[IGNORE]'){
	link_table=NULL
}else{
	link_table = read.csv(link_filename)
}

getcol = function(x){
mycols = c("black", "blue", "red", "green", "yellow", "purple", "orange", "grey", "pink", "lightblue", "darkblue", "lightgreen", "darkgreen", "darkred")
	x = x %% length(mycols)
	return(mycols[x+1])
}


plot_regions = function(t, k, imbalance){
	#title = paste("KaFFPaE Cut : ", imbalance, "% imbalance, ", k , " clusters", sep="")
	#title = paste("Ratio Cut : ", k , " clusters", sep="")
	title="Clustering of NYC Road Graph"
	print(nrow(t))
	plot(t$lon, t$lat, type="n", main=title,
		xlab="Longitude", ylab="Latitude")




	points(t$lon, t$lat, col=getcol(t$region), pch=16, cex=1)

	if(! is.null(link_table)){

		segments(x0=link_table$startX, y0=link_table$startY, x1=link_table$endX, y1=link_table$endY, lwd=1, col="black")
	}

	for(j in 0:max(t$region)){
		r = t[t$region==j,]
		mlon = median(r$lon)
		mlat = median(r$lat)

		if(getcol(j)=="black"){
			points(mlon, mlat, pch=15, cex=4, col="black")
			text(mlon, mlat, labels=j, pch=16, cex=2, col='white')
		}
		else{
			points(mlon, mlat, pch=15, cex=4, col="black")
			text(mlon, mlat, labels=j, pch=16, cex=2, col=getcol(j))
		}

	}

}








print("Reading")
bigtable = read.csv(input_filename)
bigtable$region = as.numeric(bigtable$region)
bigtable$imb = as.numeric(bigtable$imb)

print("Plotting")
pdf(output_filename)

imb_vals = sort(unique(bigtable$imbalance))
k_vals = sort(unique(bigtable$k))

for(imb in imb_vals){
	for(k in k_vals){
		print(paste("imb=",imb,"  k=",k, sep=""))
		t = bigtable[bigtable$imb==imb & bigtable$k==k,]
		plot_regions(t, k, imb)
	}
}

dev.off()


