import json
import os
from mapfunctions.utils import normalize, get_geojson_corners_coordinates


def create_multilinestring_geojson(coordinates, properties):
    """ Create a GeoJSON object with a MultiLineString geometry
    Args:
        coordinates: A list of lists of coordinates
        properties: A dictionary with the properties of the feature
    Returns:
        A GeoJSON object with a MultiLineString geometry"""

    geojson = {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "type": "MultiLineString",
            "coordinates": coordinates
        }
    }

    return geojson


def create_linestring_geojson(coordinates, properties):
    """ Create a GeoJSON object with a LineString geometry
    Args:
        coordinates: A list of lists of coordinates
        properties: A dictionary with the properties of the feature
    Returns:
        A GeoJSON object with a LineString geometry"""

    geojson = {
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates
        }
    }

    return geojson


def translate_file_lines_into_geojson(dirname, filename):
    """ Translate a file from the given directory into a GeoJSON object
    Args:
        dirname: The directory where the file is located
        filename: The name of the file
    Returns:
        A GeoJSON object with the coordinates of the file"""

    translation = {
        "type": "FeatureCollection",
        "features": []}

    with open(f"{dirname}/{filename}") as file:
        json_coordinates = json.load(file)
        for feature in json_coordinates["features"]:
            coordinates = feature["geometry"]["coordinates"]
            feature_properties = feature["properties"]
            next_multistring = []

            # Skip points
            if feature["geometry"]["type"] == "Point":
                print("\t Skipping point")
                continue

            for line in coordinates:
                next_line = []
                for point in line:
                    next_line.append([
                        normalize(point[0], 4095, 0, -4.46044921875, -4.482421875),
                        normalize(point[1], 4095, 0, 36.721273880045, 36.70365959719454)
                    ])
                next_multistring.append(next_line)

            translation["features"].append(create_multilinestring_geojson(next_multistring, feature_properties))

    return json.dumps(translation)


def translate_file_pairs_into_geojson(dirname, filename, outmin, outmax):
    """ Translate a file from the given directory into a GeoJSON object
    this function is called by 'translate_all_files_pairs' function to translate all the files in the given directory
    Args:
        dirname: The directory where the file is located
        filename: The name of the file
        outmin: The minimum coordinates of the input (to normalize)
        outmax: The maximum coordinates of the input (to normalize)
    Returns:
        A GeoJSON object with the coordinates of the file"""

    translation = {
        "type": "FeatureCollection",
        "features": []}

    with (open(f"{dirname}/{filename}") as file):
        json_coordinates = json.load(file)
        feature_id = 0
        for feature in json_coordinates["features"]:
            coordinates = feature["geometry"]["coordinates"]

            # Skip points
            if feature["geometry"]["type"] == "Point":
                print("\t Skipping point")
                continue

            for line in coordinates:
                for point_number in range(len(line) - 1):
                    next_pair = [
                        [
                            normalize(line[point_number][0], 4095, 0, outmin[0], outmax[0]),
                            normalize(line[point_number][1], 4095, 0, outmin[1], outmax[1])
                        ],
                        [
                            normalize(line[point_number + 1][0], 4095, 0, outmin[0], outmax[0]),
                            normalize(line[point_number + 1][1], 4095, 0, outmin[1], outmax[1])

                        ]
                    ]
                    feature_properties = {**feature["properties"], "feature_id": feature_id}
                    feature_id += 1
                    translation["features"].append(create_linestring_geojson(next_pair, feature_properties))

    return translation


def translate_all_files_pairs(dirname_input, outmin, outmax, dirname_output):
    """ Translate all the files in the given directory into GeoJSON objects
    Args:
        dirname_input: The directory where the files are located
        outmin: The minimum coordinates of the input (to normalize)
        outmax: The maximum coordinates of the input (to normalize)
        dirname_output: The directory where the output files will be saved"""

    number_of_files = 0
    # Open each file in the "./json_data" folder
    for filename in os.listdir(f"{dirname_input}"):
        if not filename.endswith(".json"):
            continue

        number_of_files += 1

        with open(f"{dirname_output}/{filename}", "w") as output_file:
            output_file.write(
                json.dumps(
                    translate_file_pairs_into_geojson(dirname_input, filename, outmin, outmax)
                )
            )
            print(f"File '{filename}' translated and saved on '{dirname_output}'")

def mix_tiles_from_two_folder(folder_names):
    """ Mix the files from the first two folders into the third one
    Args:
        folder_names: A list with the names of the folders"""

    for file in os.listdir(f"{folder_names[0]}"):
        with open(f"{folder_names[0]}/{file}") as file1:
            json1 = json.load(file1)

            if file in os.listdir(f"{folder_names[1]}"):
                with open(f"{folder_names[1]}/{file}") as file2:
                    json2 = json.load(file2)

                    json1["features"].extend(json2["features"])

                with open(f"{folder_names[2]}/{file}", "w") as output_file:
                    output_file.write(json.dumps(json1))
                    print(f"File '{file}' mixed and saved on '{folder_names[2]}'")


if __name__ == "__main__":
    x_tile = 7988
    y_tile = 6393
    zoom = 14

    geojson_coordinates_tile1 = get_geojson_corners_coordinates(x_tile, y_tile, zoom, format="lnglat")
    print(geojson_coordinates_tile1)
    geojson_coordinates_tile2 = get_geojson_corners_coordinates(x_tile, y_tile - 1, zoom, format="lnglat")
    print(geojson_coordinates_tile2)

    directory1 = "some_untranslated_json/tile1"
    directory2 = "some_untranslated_json/tile2"

    outmin_tile1 = [geojson_coordinates_tile1[2][0], geojson_coordinates_tile1[0][1]]
    outmax_tile1 = [geojson_coordinates_tile1[0][0], geojson_coordinates_tile1[1][1]]

    outmin_tile2 = [geojson_coordinates_tile2[2][0], geojson_coordinates_tile2[0][1]]
    outmax_tile2 = [geojson_coordinates_tile2[0][0], geojson_coordinates_tile2[1][1]]

    # get_file_geojson(directory, file)

    translate_all_files_pairs(directory1, outmin_tile1, outmax_tile1, "output_pairs/tile1")
    translate_all_files_pairs(directory2, outmin_tile2, outmax_tile2, "output_pairs/tile2")

    names = ['output_pairs/tile1', 'output_pairs/tile2', 'output_pairs/mixed']
    mix_tiles_from_two_folder(names)
