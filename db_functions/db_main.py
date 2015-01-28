"""
A small wrapper for the psycopg2 library
A database connection can be created via settings from a .conf file
And queries can be executed
"""

import psycopg2
from time import sleep

db_con = None

# Connects to a postgres database.  This must be called before execute()
# Params:
    # db_conf_file - contains the connection string
    # (which should include databse name, host, user, password)
def connect(db_conf_file, retry_interval=-1):
    #Read the connection string from the configuration file
    with open(db_conf_file, 'r') as f:
        conn_string = f.read()
    global db_con
    
    # If retry_interval >= 0, keep trying until the connection is successful
    try_again = True
    while(try_again):
        try_again = False
        try:
            # Try to connect to the database - this sets the global db_con object
            db_con = psycopg2.connect(conn_string)
            return
        except psycopg2.OperationalError as e:
            if(retry_interval >=0):
                # If the connection fails and retry_interval >=0, try again
                sleep(retry_interval)
                try_again = True
            else:
                # If the connection fails and retry_interval < 0, raise the error
                raise e
                

# Closes the connection to the database.  No more execute() queries can be run
# after the connection has been closed
def close():
    global db_con
    db_con.close()
    db_con = None

# Executes queries to an open databse connection
# Params:
    # sql - A string containing an SQL query
    # args - optional arguments for prepared statements
# Returns:
    # a new Cursor object
def execute(sql, args=None):
    global db_con
    if(db_con==None):
        raise Exception("Database is not connected.  Cannot execute query " + sql)
    cur = db_con.cursor()
    cur.execute(sql, args)
    return cur

def commit():
    db_con.commit()
