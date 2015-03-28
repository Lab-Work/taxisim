getCols = function(classes){
	motorways = c("motorway", "motorway_link")
	primary = c("primary", "primary_link")
	secondary = c("secondary", "secondary_link")
	tertiary = c("tertiary", "tertiary_link")

	#return( ifelse(classes %in% motorways, "red",
	#	ifelse(classes %in% primary, "blue",
	#	ifelse(classes %in% secondary, "green",
	#	ifelse(classes %in% tertiary, "purple",
	#	"black")))) )

	#return ( ifelse(classes %in% motorways, "red", "black") )
	return("black")
}


print("Reading")
t = read.csv("links.csv")

lowx=-74.05
hix = -73.85
lowy=40.65
hiy=40.9
plot(0,0, xlim=c(lowx,hix), ylim=c(lowy,hiy), type="n")

print("Filtering")
s = t[t$startX > lowx & t$startX < hix & t$startY > lowy & t$startY < hiy,]

print("Coloring")
cols = getCols(s$osm_class)

print("Plotting")
segments(x0=s$startX, y0=s$startY, x1=s$endX, y1=s$endY, col=cols)
