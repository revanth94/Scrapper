from pymongo import MongoClient, ASCENDING


def get_db(connection_uri="mongodb://root:rootpassword@localhost:27017/", db_name="mydatabase"):
    myclient = MongoClient(connection_uri)
    mydb = myclient[db_name]
    return mydb
