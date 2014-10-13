from math import sqrt


# TODO: Get the baseline of the normal hidden trips!
def distance(lat1, long1, lat2, long2):
    diff_lat = float(lat1) - float(lat2)
    diff_long = float(long1) - float(long2)
    # meters per degree latitude
    # an approximation based off our latitude and longitude
    lat_miles = diff_lat * 111194.86461
    # meters per degree longitude
    # an approximation  based off our latitude and longitude
    long_miles = diff_long * 84253.1418965
    return sqrt(lat_miles * lat_miles + long_miles * long_miles)
