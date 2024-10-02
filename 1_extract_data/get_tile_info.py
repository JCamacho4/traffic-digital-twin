import os
import time
import geojson

import requests
from datetime import datetime

from dotenv import load_dotenv
from osgeo import gdal

load_dotenv()


#######################################################################################################################

#######################################################################################################################

def pbf_to_json(filename, current_datetime):
    ds = gdal.OpenEx(filename, gdal.OF_VECTOR)
    gdal.VectorTranslate(filename + ".json", ds)
    gdal.VectorTranslate("dump_file_cache.json", ds)

    save_log("OK: Translation saved on file: \n\n", current_datetime)


#######################################################################################################################

#######################################################################################################################

def do_request(tomtom_url, current_datetime, folder_name):
    try:
        response = requests.get(tomtom_url)

        # Verify if the request was successful
        if response.status_code == 200:
            save_response(response.content, current_datetime, folder_name)
        else:
            raise Exception(f"ERROR on request with code: {response.status_code}")
    except Exception as e:
        # Save error on Log
        save_log(str(e), current_datetime)


def save_response(response, current_datetime, folder_name):
    filename = f"{folder_name}/{current_datetime}.pbf"

    # Write response to file
    with open(filename, "wb") as output_file:
        output_file.write(response)
        save_log("Response saved on file", current_datetime)

    pbf_to_json(filename, current_datetime)


def save_log(log, current_datetime):
    log_file = "logs.txt"

    # Write log file
    with open(log_file, "a") as archivo:
        archivo.write(f"[{current_datetime}]: {log}\n")


#######################################################################################################################

#######################################################################################################################

api_key = os.getenv("TOMTOM_API_KEY")

if __name__ == "__main__":

    # TomTom API Key
    # Zoom and coordinates of the tile
    z = 14
    x1 = 7988
    y1 = 6393

    x2 = 7988
    y2 = 6392

    # TomTom tyles Flow URL
    url1 = f"https://api.tomtom.com/traffic/map/4/tile/flow/relative/{z}/{x1}/{y1}.pbf?key={api_key}"
    url2 = f"https://api.tomtom.com/traffic/map/4/tile/flow/relative/{z}/{x2}/{y2}.pbf?key={api_key}"

    while True:
        next_file = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

        folder_name_1 = "./data/tile1"
        folder_name_2 = "./data/tile2"

        do_request(url1, next_file, folder_name_1)
        do_request(url2, next_file, folder_name_2)

        time.sleep(1800)
