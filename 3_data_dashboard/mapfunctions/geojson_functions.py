import json
import os
import osmnx as ox
import geojson

from shapely.geometry import Point

from mapfunctions.utils import float_to_hex_color, are_opposite_bearings, get_cardinal_direction_from_bearing, skip_feature
from mapfunctions.graph_functions import init_graph_point, init_graph_bbox


def __add_properties_to_feature(feature, nearest_edge, bearing_api_edge, error_management=False):
    property_error = False

    feature["properties"]["stroke-width"] = 6
    feature["properties"]["stroke"] = float_to_hex_color(feature["properties"]["traffic_level"])

    feature["properties"]["aiming"] = get_cardinal_direction_from_bearing(bearing_api_edge)
    feature["properties"]["api_bearing"] = bearing_api_edge

    feature["properties"]["nearest_edge_id"] = nearest_edge["osmid"]
    feature["properties"]["nearest_edge_length"] = nearest_edge["length"]
    feature["properties"]["nearest_edge_oneway"] = nearest_edge["oneway"]
    feature["properties"]["nearest_edge_highway"] = nearest_edge["highway"]
    feature["properties"]["nearest_edge_bearing"] = nearest_edge["bearing"]

    if "name" not in nearest_edge.keys():
        feature["properties"]["name"] = "No name"
        property_error = True
    else:
        feature["properties"]["name"] = nearest_edge["name"]

    if "maxspeed" not in nearest_edge.keys():
        feature["properties"]["maxspeed"] = "No maxspeed"
        property_error = True
    else:
        feature["properties"]["maxspeed"] = nearest_edge["maxspeed"]

    if "lanes" not in nearest_edge.keys():
        feature["properties"]["lanes"] = "No lanes"
        property_error = True
    else:
        feature["properties"]["lanes"] = nearest_edge["lanes"]

    if error_management and property_error:
        feature["properties"]["stroke"] = "#000000"


def add_info_to_file(filename, folder_input, folder_output, graph,
                     error_management=False,
                     print_distant_edges=False,
                     splits=15):
    """ Add information to the given file (splits, nearest edge, etc.)
    Args:
        filename: The name of the file
        folder_input: The folder where the file is located
        folder_output: The folder where the output file will be saved
        graph: The graph to use to get the nearest edges
        error_management: A boolean to indicate if the error management is enabled
        print_distant_edges: A boolean to indicate if the distant edges should be printed
        splits: The amount of splits to use"""

    with open(f"{folder_input}/{filename}") as f:
        data = geojson.load(f)

        middle_coordinates_lat = []
        middle_coordinates_lon = []

        coordinates_lat = []
        coordinates_lon = []

        new_features = []
        i = 0
        for feature in data["features"]:

            if skip_feature(feature):
                continue

            i += 1

            coordinates = feature["geometry"]["coordinates"]

            # We add the length of the edge to the total length
            point1 = Point(coordinates[0][1], coordinates[0][0])
            point2 = Point(coordinates[1][1], coordinates[1][0])
            length = point1.distance(point2) * 100000
            feature["properties"]["length"] = length

            coordinates_lat.append(point1.x)
            coordinates_lat.append(point2.x)

            coordinates_lon.append(point1.y)
            coordinates_lon.append(point2.y)

            # Get the middle of both points
            middle_point = ((point1.x + point2.x) / 2, (point1.y + point2.y) / 2)
            middle_coordinates_lon.append(middle_point[1])
            middle_coordinates_lat.append(middle_point[0])

        nearest_edges_and_distance_list = ox.distance.nearest_edges(graph, middle_coordinates_lon,
                                                                    middle_coordinates_lat, return_dist=True)

        if len(nearest_edges_and_distance_list[0]) != i:
            raise ValueError("ERROR: Different number of features and nearest edges")

        nearest_edges_list = nearest_edges_and_distance_list[0]
        nearest_distance_list = nearest_edges_and_distance_list[1]

        j = 0
        for feature in data["features"]:

            if skip_feature(feature):
                continue

            nearest_edge_id = nearest_edges_list[j]
            feature["properties"]["error"] = ""
            distance_in_meters = nearest_distance_list[j] * 100000

            if distance_in_meters > 10:
                feature["properties"]["error"] = "Very distant from the nearest edge"

                if print_distant_edges:
                    print(
                        f"Feature {j} (edge{nearest_edge_id}) is very distant from the nearest edge: "
                        f"{distance_in_meters} meters -> {[middle_coordinates_lat[j], middle_coordinates_lon[j]]}")

                j += 1
                continue

            nearest_edge = graph.edges[nearest_edge_id]

            bearing_api_edge = ox.bearing.calculate_bearing(coordinates_lat[j * 2], coordinates_lon[j * 2],
                                                            coordinates_lat[j * 2 + 1], coordinates_lon[j * 2 + 1])

            # Check if the direction is reversed or not
            if are_opposite_bearings(nearest_edge["bearing"], bearing_api_edge, tolerance=45):
                feature["properties"]["nearest_edge_reverse"] = not nearest_edge["reversed"]
            else:
                feature["properties"]["nearest_edge_reverse"] = nearest_edge["reversed"]

            # Once we know the nearest edge, we check if the API edge needs to be split
            amount_splits = round(feature["properties"]["length"] / splits)

            if 'junction' in nearest_edge.keys() and nearest_edge["junction"] == "roundabout":
                feature["properties"]["splits"] = 0
                feature["properties"]["junction"] = nearest_edge["junction"]
            else:
                feature["properties"]["splits"] = amount_splits

            __add_properties_to_feature(feature, nearest_edge, bearing_api_edge, error_management=error_management)

            j += 1

            new_features.append(feature)

        res = {
            "type": "FeatureCollection",
            # "features": data["features"]
            "features": new_features

        }

        json.dump(res, open(f"{folder_output}/{filename}", "w"))


def add_info_to_folder(folder_input, folder_output, graph,
                       error_management=False,
                       print_distant_edges=False,
                       splits=15):
    """ Add information to all the files in the given folder (splits, nearest edge, etc.)
    Args:
        folder_input: The folder where the files are located
        folder_output: The folder where the output files will be saved
        graph: The graph to use to get the nearest edges
        error_management: A boolean to indicate if the error management is enabled
        print_distant_edges: A boolean to indicate if the distant edges should be printed"""

    for filename in os.listdir(folder_input):
        if filename.endswith(".json"):
            print(f"Adding information to {filename}")
            add_info_to_file(filename, folder_input, folder_output, graph,
                             error_management=error_management,
                             print_distant_edges=print_distant_edges,
                             splits=splits)


if __name__ == "__main__":
    # Center of tile1
    lat = 36.71341846443054
    lon = -4.472105013872079
    dist = 1300

    # Center of the two tiles
    lat = 36.721273880045
    lon = -4.47143554688
    dist = 1600

    G = init_graph_point(lat, lon, dist)

    north = 36.711573
    south = 36.728257
    east = -4.489825
    west = -4.458990

    G = init_graph_bbox(north, south, east, west)

    # name = "2024_04_30_23_32_28.pbf.json"
    # folder_i = "output_pairs/tile1"
    # folder_o = "output_add_info/tile1"
    # add_info_to_file(name, folder_i, folder_o, G, splits=5)

    folder_input = "output_pairs/mixed"
    folder_output = "output_add_info/mixed"
    add_info_to_folder(folder_input, folder_output, G, splits=15)
