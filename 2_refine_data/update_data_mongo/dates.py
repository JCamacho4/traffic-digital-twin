import json
import os
from datetime import datetime


def get_files_dictionary_from_folder(path):
    # Get the list of files in the folder
    files = os.listdir(path)

    available_files = []
    # Iterate over the files in the folder
    for file in files:
        # Check if file is .pbf.json
        if not file.endswith(".json"):
            continue

        next_file = {"filename_extensions": file, "filename": file.split(".")[0],
                     "datetime": datetime.strptime(file.split(".")[0], "%Y_%m_%d_%H_%M_%S")}
        next_file["day_of_week"] = next_file["datetime"].strftime("%A")

        available_files.append(next_file)

    return available_files
