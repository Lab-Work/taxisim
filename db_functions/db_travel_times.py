# -*- coding: utf-8 -*-
"""
Contains functions for loading and saving the travel times of Links
into the database
Created on Fri Jan  9 15:08:51 2015

@author: brian
"""

import db_main

# Creates the table which stores travel time data
def create_travel_time_table():
    sql = """CREATE TABLE travel_times (
        begin_node_id BIGINT, 
        end_node_id BIGINT,
        datetime TIMESTAMP,
        travel_time REAL,
        num_trips INTEGER);"""
    db_main.execute(sql)
    
    sql = "CREATE INDEX idx_tt_datetime ON travel_times using BTREE (datetime);"
    db_main.execute(sql)

def drop_travel_time_table():
    db_main.execute("DROP TABLE travel_times;")


def load_travel_times(road_map, datetime):
    # Execute the query
    sql = "SELECT * FROM travel_times where datetime==%s;"
    cur = db_main.execute(sql, (datetime,))
    
    # Iterate through the cursor returned by the query
    for (begin_node_id, end_node_id, datetime, travel_time, speed, num_trips) in cur:
        # Find the appropriate Link in the road_map and set the relevant attributes
        if((begin_node_id, end_node_id) in road_map.links_by_node_id):
            link = road_map.links_by_node_id[begin_node_id, end_node_id]
            link.time = travel_time
            link.speed = link.length / travel_time
            link.num_trips = num_trips
    cur.close()


def save_travel_times(road_map, datetime):
    BULK_SIZE=5000
    # Create a prepared statement
    db_main.execute("PREPARE tt_plan (BIGINT, BIGINT, DATETIME, REAL, INTEGER) AS "
    "INSERT INTO travel_times VALUES($1, $2, $3, $4, $5);")
    
    sqls = []
    date_str = str(datetime)
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
