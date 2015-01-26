# -*- coding: utf-8 -*-
"""
Contains functions for loading and saving the travel times of Links
into the database
Created on Fri Jan  9 15:08:51 2015

@author: Brian Donovan (briandonovan100@gmail.com)
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
    try:
        db_main.execute(sql)
        sql = "CREATE INDEX idx_tt_datetime ON travel_times using BTREE (datetime);"
        db_main.execute(sql)
    except:
        pass
    db_main.commit()

# Drops the table that stores travel time data
def drop_travel_time_table():
    try:
        db_main.execute("DROP TABLE travel_times;")
        db_main.commit()
    except:
        pass



# Removes any travel time estimates from the database for a particular datetime
# Params:
    # datetime - all travel time estimates with this time will be deleted
def delete_travel_times(datetime):
    sql = "DELETE FROM travel_times where datetime=%s;"
    db_main.execute(sql, (datetime,))
    db_main.commit()


def get_travel_time_table_size():
    sql = "SELECT pg_size_pretty(pg_total_relation_size('travel_times'));"
    cur = db_main.execute(sql)
    [size] = cur
    return size
    


# Saves traffic conditions (link-by-link travel times) from a Map object into the
# database.  If there are already travel times saved for the given time, they will
# be overwritten.
# Params:
    # road_map - a Map object, which contains the travel times on its Links
    # datetime - the time at which these traffic conditions occur
def save_travel_times(road_map, datetime):
    date_str = "'" + str(datetime) + "'"
    
    # First remove any existing travel times for the given datetime
    delete_travel_times(datetime)  
    
    # Next, add one row with the default speed.  This will have nodes 0, 0
    # The default speed will be saved in the travel time field
    default_speed = road_map.get_default_speed()
    if(default_speed!=None):
        sql = "INSERT INTO travel_times VALUES(0, 0, %s, %f, 0);" % (date_str, default_speed)
        db_main.execute(sql)
    
    
    BULK_SIZE=5000
    # Create a prepared statement
    db_main.execute("PREPARE tt_plan (BIGINT, BIGINT, TIMESTAMP, REAL, INTEGER) AS "
    "INSERT INTO travel_times VALUES($1, $2, $3, $4, $5);")
    
    sqls = []
    
    # Loop through the Links and create a bunch of EXECUTE statements
    for link in road_map.links:
        if(link.num_trips > 0):
            sql = "EXECUTE tt_plan(%d, %d, %s, %f, %d);" % (
                link.origin_node_id, link.connecting_node_id, date_str, link.time, link.num_trips)
            sqls.append(sql)
        if(len(sqls) >= BULK_SIZE):
            # Concatenate EXECUTE statements and run them
            final_sql = "\n".join(sqls)
            sqls = []
            db_main.execute(final_sql)
            db_main.commit()
    
    # Run the last few EXECUTE statements if necessary
    if(len(sqls) > 1):
        final_sql = "\n".join(sqls)
        db_main.execute(final_sql)
        db_main.commit()
    
    # Clean up the prepared statement
    db_main.execute("DEALLOCATE tt_plan;")
    db_main.commit()



# Helper method, which 
def get_travel_times_cursor(datetime):
    # Execute the query
    sql = "SELECT * FROM travel_times where datetime=%s ORDER BY (begin_node_id, end_node_id);"
    cur = db_main.execute(sql, (datetime,))
    return cur



# Loads traffic conditions (link-by-link travel times) from the database and applies them onto
# of a Map object.  After this is called, Link.time, Link.speed, and Link.num_trips
# will be set for every Link in the Map.
# Params:
    # road_map - a Map object, to be modified
    # datetime - Traffic conditions for this date/time will be loaded
def load_travel_times(road_map, datetime):
    
      
    
    # Execute the query
    cur = get_travel_times_cursor(datetime)
    
    i = 0
    # Iterate through the cursor returned by the query
    for (begin_node_id, end_node_id, datetime, travel_time, num_trips) in cur:
        
        # If there is a default entry, it will be the first one
        # Set all of the links using this entry
        if(begin_node_id==0 and end_node_id==0):
            # In this case, the travel_time field holds the speed
            road_map.set_all_link_speeds(travel_time)
                
            
        i += 1
        # Find the appropriate Link in the road_map and set the relevant attributes
        if((begin_node_id, end_node_id) in road_map.links_by_node_id):
            link = road_map.links_by_node_id[begin_node_id, end_node_id]
            link.time = travel_time
            link.speed = link.length / travel_time
            link.num_trips = num_trips
    cur.close()
    
    #print("Loaded " + str(i) + " records.")