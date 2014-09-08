from aStar import aStar
import csv

#TODO: Get the baseline of the normal hidden trips!
def distance(lat1, long1, lat2, long2):
	diffLat = float(lat1) - float(lat2)
	diffLong = float(long1) - float(long2)
	latMiles = diffLat * 111194.86461 #meters per degree latitude, an approximation  based off our latitude and longitude
	longMiles = diffLong * 84253.1418965 #meters per degree longitude, an approximation  based off our latitude and longitude
	return sqrt(latMiles * latMiles + longMiles * longMiles)

