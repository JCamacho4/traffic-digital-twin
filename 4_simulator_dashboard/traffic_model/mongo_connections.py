from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


def get_database(database_name="TFG"):
    # Create a connection using MongoClient
    client = MongoClient(os.getenv("MONGO_URI"))

    # Create the database if it doesn't exist, otherwise return the existing database
    return client[database_name]


def get_edges_by_filename(db, filename):
    mongo_object = db["graphs"].find_one({"filename": filename})
    if mongo_object:
        return mongo_object["links"]
    else:
        return None
