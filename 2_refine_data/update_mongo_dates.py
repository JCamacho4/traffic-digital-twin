import update_data_mongo.dates as mongo_dates
import update_data_mongo.mongo as mongo

if __name__ == "__main__":
    mixed_tiles_path = "output_split/mixed"

    available_files_info = mongo_dates.get_files_dictionary_from_folder(mixed_tiles_path)
    mongo.insert_multiple_data(mongo.get_database()["dates"], available_files_info)
