# -*- coding: utf-8 -*-
"""
Contains the Trip class, which represents a single taxi trip.

Created on Wed Aug  6 14:17:57 2014

@author: Brian Donovan (briandonovan100@gmail.com)
"""
#from tools import *
from routing.Node import approx_distance



#A single taxi trip - contains information such as coordinates, times, etc...
#Can be parsed from a line of a CSV file via the constructor
#Some trips contain obvious errors - the isValid() method reveals this
class Trip:
    header_line = []

    #A static method which enables the __init__() method to work properly
    #Given the header line from a CSV file, it determines the index of each column (by name)
    @staticmethod
    def initHeader(header):
        Trip.header_line = header
        Trip.header = {} #Maps header names to column index
        for i in range(len(header)):
            Trip.header[header[i].strip()] = i
    
    #Constructs a Trip object using a line from a CSV file.  Assumes that Trip.initHeader() has already been called
    #Arguments:
        #csvLine - A list, which has been parsed from a CSV data file
    def __init__(self, record):
        #Store the actual data in case we need it later...
        #self.csvLine = csvLine
        
        [medallion, hack_license, vendor_id, rate_code, store_and_fwd_flag, pickup_datetime, dropoff_datetime, passenger_count, trip_time_in_secs, trip_distance, pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude, payment_type, fare_amount, surcharge, mta_tax, tip_amount, tolls_amount, pickup_geom, dropoff_geom, day_of_week, hours_of_day] = record
                 

        try:
            [self.fromLon, self.fromLat, self.toLon, self.toLat, self.dist] = map(float, 
                    [pickup_longitude, pickup_latitude, dropoff_longitude, dropoff_latitude, trip_distance])
        except:
            [self.fromLon, self.fromLat, self.toLon, self.toLat, self.dist] = 0
        self.dist *= 1609.34 # convert to meters
    
        self.pickup_time = pickup_datetime
        self.dropoff_time = dropoff_datetime



        duration = self.dropoff_time - self.pickup_time  #Dropoff time is used to compute duration (timedelta object)
        self.time = int(duration.total_seconds()) #Time stores the duration as seconds
        
        #For traffic estimation algorithm
        self.path_links = None
        self.path_link_ids = None
        self.dup_times = None
        self.estimated_time = 0.0
        self.estimate_distance = 0.0
  

  
  
  
        #Compute pace (if possible)
        if(self.dist==0):
            self.pace = 0
        else:
            self.pace = float(self.time) / self.dist        
        
    
        #Straightline distance between pickup and dropoff coordinates        
        self.straight_line_dist = approx_distance(self.fromLat, self.fromLon,self.toLat, self.toLon)
        
        #Winding factor = ratio of true distance over straightline distance (typically something like 1.5)
        if(self.straight_line_dist<=0):
            self.winding_factor = 1
        else:
            self.winding_factor = self.dist / self.straight_line_dist
        
        self.has_other_error=False

    def displayTrip(self):
        print "Medallion:\t\t\t\t", self.medallion, "\nHack license:\t\t\t\t", self.hack_license, "\nVendor ID:\t\t\t\t", self.vendor_id, rate_code, "\nRate code:\t\t\t\t", self.rate_code, "\nStore and fwd flag:\t\t\t", self.store_and_fwd_flag, "\nPickup datetime:\t\t\t", self.pickup_datetime, "\nDropoff datetime:\t\t\t", self.dropoff_datetime, "\nPassenger count:\t\t\t", self.passenger_count, "\nTrip time in secs:\t\t\t", self.trip_time_in_secs, "\nTrip distance:\t\t\t\t", self.trip_distance, "\nPickup longitude:\t\t\t", self.pickup_longitude, "\nPickup latitude:\t\t\t", self.pickup_latitude, "\nDropoff longitude:\t\t\t", self.dropoff_longitude, "\nDropoff latitude:\t\t\t", self.dropoff_latitude, "\nPayment type:\t\t\t\t", self.payment_type, "\nFare amount:\t\t\t\t", self.fare_amount, "\nSurcharge:\t\t\t\t", self.surcharge, "\nMTA tax:\t\t\t\t", self.mta_tax, "\nTip amount:\t\t\t\t", self.tip_amount, "\nTolls amount:\t\t\t\t", self.tolls_amount
    
    #All of the different types of errors that could occur - most are based on thresholds
    #An ERROR trip is one that is clearly impossible (e.g. a winding factor of .5, which violates Euclidean geometry)
    #A BAD trip is one that is technically possible, but not useful for our analysis (e.g. a 10-second trip)
    VALID = 0
    BAD_GPS = 1
    ERR_GPS = 2
    BAD_LO_STRAIGHTLINE=3
    BAD_HI_STRAIGHTLINE=4
    ERR_LO_STRAIGHTLINE=5
    ERR_HI_STRAIGHTLINE=6
    BAD_LO_DIST=7
    BAD_HI_DIST=8
    ERR_LO_DIST=8
    ERR_HI_DIST=10    
    BAD_LO_WIND=11
    BAD_HI_WIND=12
    ERR_LO_WIND=13
    ERR_HI_WIND=14    
    BAD_LO_TIME=15
    BAD_HI_TIME=16
    ERR_LO_TIME=17
    ERR_HI_TIME=18    
    BAD_LO_PACE=19
    BAD_HI_PACE=20
    ERR_LO_PACE=21
    ERR_HI_PACE=22
    ERR_DATE = 23
    ERR_OTHER = 24
    
    #This method implements data filtering
    #Tells whether the trip is valid, by applying various thresholds to the features.
    #Returns: An integer error code.  0 means it is a valid trip, 1-24 are different types of errors, listed above
    def isValid(self):
        #These two months contain a very high number of errors, so they cannot be trusted
        if(self.pickup_time.year==2010 and self.pickup_time.month==8):
            return Trip.ERR_DATE
        if(self.pickup_time.year==2010 and self.pickup_time.month==9):
            return Trip.ERR_DATE
        
        
        #First filter obvious errors
        
        #GPS coordinates (in degrees) not reasonable
        if(self.toLat < 40.4 or self.fromLat < 40.4):
            return Trip.ERR_GPS
        if(self.toLat > 41.1 or self.fromLat > 41.1):
            return Trip.ERR_GPS
        if(self.toLon < -74.25 or self.fromLon < -74.25):
            return Trip.ERR_GPS
        if(self.toLon > -73.5 or self.fromLon > -73.5):
            return Trip.ERR_GPS

        #Distance between start and end coordinates (in miles) not reasonable
        if(self.straight_line_dist < .001*1609.34):
            return Trip.ERR_LO_STRAIGHTLINE
        if(self.straight_line_dist > 20*1609.34):
            return Trip.ERR_HI_STRAIGHTLINE
                
        #Metered distance (in miles) not reasonable
        if(self.dist < .001*1609.34):
            return Trip.ERR_LO_DIST
        if(self.dist > 20*1609.34):
            return Trip.ERR_HI_DIST
        
        #In euclidean space, the winding factor (metered dist / straightline dist) must be >= 1
        #We allow some small room for rounding errors and GPS noise
        if(self.winding_factor < .95):
            return Trip.ERR_LO_WIND

        #Unreasonable trip time (in seconds)
        if(self.time < 10):
            return Trip.ERR_LO_TIME
        if(self.time > 7200):
            return Trip.ERR_HI_TIME
        
        #Unreasonable pace (in second/meter)
        if(self.pace < 10/1609.34):
            return Trip.ERR_LO_PACE
        if(self.pace > 7200/1609.34):
            return Trip.ERR_HI_PACE
        
        
        #Next filter data that is not necessarily an error
        #But is still not useful for the analysis
        
        #Restrict analysis to Manhattan and a small surrounding area
        if(self.toLat < 40.6 or self.fromLat < 40.6):
            return Trip.BAD_GPS
        if(self.toLat > 40.9 or self.fromLat > 40.9):
            return Trip.BAD_GPS
        if(self.toLon < -74.05 or self.fromLon < -74.05):
            return Trip.BAD_GPS
        if(self.toLon > -73.7 or self.fromLon > -73.7):
            return Trip.BAD_GPS
        
        #Really long trips (in miles) are not representative
        if(self.straight_line_dist > 8*1609.34):
            return Trip.BAD_HI_STRAIGHTLINE
                
        if(self.dist > 15*1609.34):
            return Trip.BAD_HI_DIST
        
        #A high winding factor indicates that the taxi did not proceed directly to its destination
        #So it is not representative of its start and end regions
        if(self.winding_factor > 5):
            return Trip.BAD_HI_WIND
            
        #Really short or really long trips are not representative
        if(self.time < 60):
            return Trip.BAD_LO_TIME
        if(self.time > 3600):
            return Trip.BAD_HI_TIME
        
        #These speeds are technically possible, but not indicative of overall traffic
        if(self.pace < 40/1609.34):
            return Trip.BAD_LO_PACE
        if(self.pace > 3600/1609.34):
            return Trip.BAD_HI_PACE

        
        return Trip.VALID
    
    # Replaces references to graph objects (Nodes, Links) with id numbers.
    # This way, the Trip can be pickled and, for example, sent to a worker process
    def flatten(self):
        #Replace nodes with node ids
        if(self.origin_node != None):
            self.origin_node_id = self.origin_node.node_id
            self.dest_node_id = self.dest_node.node_id
            self.origin_node = None
            self.dest_node = None
        #Replace links with link ids
        if(self.path_links != None):
            self.path_link_ids = [link.link_id for link in self.path_links]
            self.path_links = None
    
    # Undoes the flatten() operation using a Map object.  ID numbers of graph objects
    # are replaced with references to those objects
    def unflatten(self, road_map):
        #replace node ids with nodes
        if(self.origin_node_id != None):
            self.origin_node = road_map.nodes_by_id[self.origin_node_id]
            self.dest_node = road_map.nodes_by_id[self.dest_node_id]
        
        #replace link ids with links
        if(self.path_link_ids != None):
            self.path_links = [road_map.links[_id] for _id in self.path_link_ids]            
        

    #For debugging
    def __str__(self):
        
        s = "<<TRIP>>\n" + "driver " + self.driver_id + "\ntime " + str(self.time) + "\n" + "dist " + str(self.dist) + "\n"
        return s
