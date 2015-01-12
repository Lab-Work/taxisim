"""
A small wrapper for the psycopg2 library
A database connection can be created via settings from a .conf file
And queries can be executed
"""

import psycopg2


db_con = None

# Connects to a postgres database.  This must be called before execute()
# Params:
    # db_conf_file - contains the connection string
    # (which should include databse name, host, user, password)
def connect(db_conf_file):
    #Read the connection string from the configuration file
    with open(db_conf_file, 'r') as f:
        conn_string = f.read()
    #Set the connection object
    global db_con
    db_con = psycopg2.connect(conn_string)

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
