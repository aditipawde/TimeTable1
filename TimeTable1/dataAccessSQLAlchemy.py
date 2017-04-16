import sqlalchemy as sql
import pymysql as py
import pandas as pd



# Class for conencting to database
class DB:

    def getConnection (self):
        engine = sql.create_engine('mysql+pymysql://root:pedha@localhost/timeTable');

        #print(engine.table_names());
        con = engine.connect();
        return con;

    def close (self,con):
        con.close();


# Initialization method to initialize all frames
def initialize (table_name):
    db = DB();
    
    con = db.getConnection();
    frame = pd.read_sql_table(table_name, con);

    db.close(con);

    return frame;


def execquery (query):
    db = DB()
    con = db.getConnection()


    frame = pd.read_sql_query(query, con)

    db.close(con)

    return frame;

