pdf("ratio_cut_clusters.pdf")
for(k in 2:10){
	filename = paste("tmp_clusters_",k,".csv", sep="")
	t = read.csv(filename)
	title = paste("Ratio cut : ", k , " clusters")
	plot(t$lon, t$lat, col=t$region+1, pch=16, cex=.5, main=title)

}
dev.off()



pdf("ncut_clusters.pdf")
for(k in 2:10){
	filename = paste("ncut_clusters_",k,".csv", sep="")
	t = read.csv(filename)
	title = paste("N cut : ", k , " clusters")
	plot(t$lon, t$lat, col=t$region+1, pch=16, cex=.5, main=title)

}
dev.off()

pdf("weight_clusters.pdf")
for(k in 2:10){
	filename = paste("weight_clusters_",k,".csv", sep="")
	t = read.csv(filename)
	title = paste("Weighted Ratio Cut : ", k , " clusters")
	plot(t$lon, t$lat, col=t$region+1, pch=16, cex=.5, main=title)

}
dev.off()
