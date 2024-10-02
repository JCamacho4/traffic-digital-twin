import datetime
from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv

load_dotenv()

CONNECTION_STRING = os.getenv("CONNECTION_STRING")


def get_database(database_name="TFG"):
    # Create a connection using MongoClient
    client = MongoClient(CONNECTION_STRING)

    # Create the database if it doesn't exist, otherwise return the existing database
    return client[database_name]


def insert_data(collection, data):
    # Insert data into the collection
    collection.insert_one(data)


def insert_multiple_data(collection, data_list):
    # Insert multiple data into the collection
    collection.insert_many(data_list)


def insert_file(collection, file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        insert_data(collection, data)


def insert_multiple_files(collection, file_paths):
    for file_path in file_paths:
        insert_file(collection, file_path)


if __name__ == "__main__":
    db = get_database("TFG")

    dates_collection = db["dates"]

    date_test = {'filename_extensions': '2024_05_08_16_19_06.pbf.json', 'filename': '2024_05_08_16_19_06',
                 'datetime': datetime.datetime(2024, 5, 8, 16, 19, 6), 'day_of_week': 'Wednesday'}
    # insert_data(dates_collection, date_test)
