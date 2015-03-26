# -*- coding: utf-8 -*-
"""
Contains functions for loading and saving the arcflags of Links
into the database
Created on Fri Jan  9 15:08:51 2015
@author: Brian Donovan (briandonovan100@gmail.com)
"""


import db_functions.db_main as db_main

# Creates the table which stores arcflag data
def create_arc_flag_table():
    
    sql = """CREATE TABLE arc_flags (
        begin_node_id BIGINT, 
        end_node_id BIGINT,
        datetime TIMESTAMP,
        arc_flag_forward varchar(200),
        arc_flag_backward varchar(200));"""  #___________________HERE______________________
    try:
        db_main.execute(sql)
        sql = "CREATE INDEX idx_af_datetime ON arc_flags using BTREE (datetime);"
        db_main.execute(sql)
    except:
        pass
    db_main.commit()
    

# Drops the table that stores arcflag data
def drop_arc_flag_table():
    try:
        db_main.execute("DROP TABLE arc_flags;")
    except:
        pass
    db_main.commit()



# Removes any arcflag estimates from the database for a particular datetime
# Params:
    # datetime - all arcflag estimates with this time will be deleted
def delete_arc_flags(datetime):
    sql = "DELETE FROM arc_flags where datetime=%s;"
    db_main.execute(sql, (datetime,))
    db_main.commit()


def get_arc_flag_table_size():
    sql = "SELECT pg_size_pretty(pg_total_relation_size('arc_flags'));"
    cur = db_main.execute(sql)
    [size] = cur
    return size

# Returns a sorted list of datetimes where arcflag information is available
def get_available_dates():
    sql = "SELECT DISTINCT datetime FROM arc_flags ORDER BY datetime;"
    cur = db_main.execute(sql)
    dates = [date for (date,) in cur]
    return dates


# Saves traffic conditions (link-by-link arcflags) from a Map object into the
# database.  If there are already arcflags saved for the given time, they will
# be overwritten.
# Params:
    # road_map - a Map object, which contains the arcflags on its Links
    # datetime - the time at which these traffic conditions occur
def save_arc_flags(road_map, datetime):
    date_str = "'" + str(datetime) + "'"
    
    # First remove any existing arcflags for the given datetime
    delete_arc_flags(datetime)  
    
    # Next, add one row with the default speed.  This will have nodes 0, 0
    # The default speed will be saved in the arcflag field
    sql = "INSERT INTO arc_flags VALUES(0, 0, %s, 0, 0);" % (date_str) #___________________HERE______________________
    db_main.execute(sql)
    
    
    BULK_SIZE=5000
    # Create a prepared statement
    db_main.execute("PREPARE af_plan (BIGINT, BIGINT, TIMESTAMP, varchar(200), varchar(200)) AS "
    "INSERT INTO arc_flags VALUES($1, $2, $3, $4, $5);") #___________________HERE______________________
    
    sqls = []
    
    # Loop through the Links and create a bunch of EXECUTE statements
    for link in road_map.links:
        sql = "EXECUTE af_plan(%d, %d, %s, %s, %s);" % (
            link.origin_node_id, link.connecting_node_id, date_str, "\'" + link.get_forward_arcflags_hex() + "\'", "\'" + link.get_backward_arcflags_hex() + "\'") #___________________HERE______________________
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
    db_main.execute("DEALLOCATE af_plan;")
    db_main.commit()



# Helper method, which 
def get_arc_flags_cursor(datetime):
    # Execute the query
    sql = "SELECT * FROM arc_flags where datetime=%s ORDER BY (begin_node_id, end_node_id);"
    cur = db_main.execute(sql, (datetime,))
    return cur



# Loads traffic conditions (link-by-link arcflags) from the database and applies them onto
# of a Map object.  After this is called, Link.time, Link.speed, and Link.num_trips
# will be set for every Link in the Map.
# Params:
    # road_map - a Map object, to be modified
    # datetime - Traffic conditions for this date/time will be loaded
def load_arc_flags(road_map, datetime):
      
    
    # Execute the query
    cur = get_arc_flags_cursor(datetime)
    
    i = 0
    # Iterate through the cursor returned by the query
    for (begin_node_id, end_node_id, datetime, forward_arcs, backward_arcs) in cur:
        
        # If there is a default entry, it will be the first one
        # Set all of the links using this entry
        # if(begin_node_id==0 and end_node_id==0):
            # In this case, the travel_time field holds the speed
            # road_map.set_all_link_speeds(travel_time)
                
        i += 1
        # Find the appropriate Link in the road_map and set the relevant attributes
        if((begin_node_id, end_node_id) in road_map.links_by_node_id):
            link = road_map.links_by_node_id[begin_node_id, end_node_id]
            link.decode_forward_arcflags_hex(forward_arcs) #___________________HERE______________________
            link.decode_backward_arcflags_hex(backward_arcs) #___________________HERE______________________
            # link.speed = link.length / travel_time
    cur.close()
    
    #print("Loaded " + str(i) + " records.")



def create_link_counts_table():
    sql = """CREATE TABLE link_counts (
        begin_node_id BIGINT,
        end_node_id BIGINT,
        avg_num_trips FLOAT);"""
    
    try:
        db_main.execute(sql)
    except:
        print "Error creating link counts table."
    db_main.commit()


def save_link_counts(count_dict):
    sqls = []
    for (begin_node_id, end_node_id) in count_dict:
        count = count_dict[(begin_node_id, end_node_id)]
        
        sql = "INSERT INTO link_counts VALUES(%d,%d,%f);" % (
            begin_node_id,end_node_id,count)
        sqls.append(sql)
    
    db_main.execute("DELETE FROM link_counts;")
    db_main.execute("\n".join(sqls))
    db_main.commit()

# Helper method, which 
def get_link_counts_cursor():
    # Execute the query
    sql = "SELECT * FROM link_counts;"
    cur = db_main.execute(sql)
    return cur
