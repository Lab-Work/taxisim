# -*- coding: utf-8 -*-
"""
Contains functions for loading and saving the travel times of Links
into the database
Created on Fri Jan  9 15:08:51 2015

@author: Brian Donovan (briandonovan100@gmail.com)
"""

# TODO : Don't save all of the Links that have 0 trips on them, because they all have a default travel time
# This redundant information accounts for ~95% of the data

import db_main

# Creates the table which stores travel time data
def create_travel_time_table():
    
    sql = """CREATE TABLE travel_times (
        begin_node_id BIGINT, 
        end_node_id BIGINT,
        datetime TIMESTAMP,
        travel_time REAL,
        num_trips INTEGER);"""
    try:
        db_main.execute(sql)
        sql = "CREATE INDEX idx_tt_datetime ON travel_times using BTREE (datetime);"
        db_main.execute(sql)
    except:
        pass
    db_main.commit()

# Drops the table that stores travel time data
def drop_travel_time_table():
    db_main.execute("DROP TABLE travel_times;")
    db_main.commit()


# Loads traffic conditions (link-by-link travel times) from the database and applies them onto
# of a Map object.  After this is called, Link.time, Link.speed, and Link.num_trips
# will be set for every Link in the Map.
# Params:
    # road_map - a Map object, to be modified
    # datetime - Traffic conditions for this date/time will be loaded
def load_travel_times(road_map, datetime):
    # Execute the query
    sql = "SELECT * FROM travel_times where datetime=%s;"
    cur = db_main.execute(sql, (datetime,))
    
    i = 0
    # Iterate through the cursor returned by the query
    for (begin_node_id, end_node_id, datetime, travel_time, num_trips) in cur:
        i += 1
        # Find the appropriate Link in the road_map and set the relevant attributes
        if((begin_node_id, end_node_id) in road_map.links_by_node_id):
            link = road_map.links_by_node_id[begin_node_id, end_node_id]
            link.time = travel_time
            link.speed = link.length / travel_time
            link.num_trips = num_trips
    cur.close()
    
    #print("Loaded " + str(i) + " records.")

# Saves traffic conditions (link-by-link travel times) from a Map object into the
# database.
# Params:
    # road_map - a Map object, which contains the travel times on its Links
    # datetime - the time at which these traffic conditions occur
def save_travel_times(road_map, datetime):
    BULK_SIZE=5000
    # Create a prepared statement
    db_main.execute("PREPARE tt_plan (BIGINT, BIGINT, TIMESTAMP, REAL, INTEGER) AS "
    "INSERT INTO travel_times VALUES($1, $2, $3, $4, $5);")
    
    sqls = []
    date_str = "'" + str(datetime) + "'"
    # Loop through the Links and create a bunch of EXECUTE statements
    for link in road_map.links:
        sql = "EXECUTE tt_plan(%d, %d, %s, %f, %d);" % (
            link.origin_node_id, link.connecting_node_id, date_str, link.time, link.num_trips)
        sqls.append(sql)
        if(len(sqls) >= BULK_SIZE):
            # Concatenate EXECUTE statements and run them
            final_sql = "\n".join(sqls)
            sqls = []
            db_main.execute(final_sql)
            db_main.commit()
    
    # Run the last few EXECUTE statements
    final_sql = "\n".join(sqls)
    db_main.execute(final_sql)
    db_main.commit()

