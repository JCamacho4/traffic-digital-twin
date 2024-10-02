import json
import os

import osmnx as ox
import geojson
from matplotlib import pyplot as plt
import networkx as nx

from mapfunctions import constants
from mapfunctions.utils import are_opposite_bearings, skip_feature


def add_osmnx_info(graph):
    """ Add the osmnx info to the graph
    Args:
        graph: The graph to add the info
    Returns:
        The graph with the info added"""

    graph = ox.bearing.add_edge_bearings(graph)
    graph = ox.distance.add_edge_lengths(graph)
    graph = ox.routing.add_edge_speeds(graph)
    graph = ox.routing.add_edge_travel_times(graph)

    return graph


def remove_edges(graph, osm_ways_to_delete):
    """ Remove the edges from the graph
    Args:
        graph: The graph to remove the edges
        osm_ways_to_delete: The list with the way's OSM id to delete
    Returns:
        The graph with the edges removed """

    edges_to_delete = []
    for u, v, data in graph.edges(data=True):
        if data['osmid'] in osm_ways_to_delete:
            edges_to_delete.append((u, v))

    graph.remove_edges_from(edges_to_delete)

    isolated_nodes = list(nx.isolates(graph))
    graph.remove_nodes_from(isolated_nodes)

    return graph


def init_graph_point(latitude, longitude, dist, osm_ways_to_delete=None):
    """ Initialize a graph from a point
    Args:
        latitude: The latitude of the point
        longitude: The longitude of the point
        dist: The distance to get the graph
        osm_ways_to_delete: The list with the way's OSM id to delete
    Returns:
        The graph initialized from the point"""

    graph = ox.graph_from_point((latitude, longitude),
                                dist=dist,
                                network_type='drive',
                                simplify=False)

    for u, v, edge_data in graph.edges(data=True):
        edge_data["dates"] = {}

    graph = add_osmnx_info(graph)

    if osm_ways_to_delete is not None:
        graph = remove_edges(graph, osm_ways_to_delete)

    return __setup_maxspeed(graph)


def init_graph_bbox(north, south, east, west, osm_ways_to_delete=None):
    """ Initialize a graph from a bbox
    Args:
        north: The north latitude
        south: The south latitude
        east: The east longitude
        west: The west longitude
        osm_ways_to_delete: The list with the way's OSM id to delete
    Returns:
        The graph initialized from the bbox"""

    graph = ox.graph_from_bbox(bbox=(north, south, east, west),
                               network_type='drive',
                               simplify=False,
                               truncate_by_edge=True)

    for u, v, edge_data in graph.edges(data=True):
        edge_data["dates"] = {}

    graph = add_osmnx_info(graph)

    if osm_ways_to_delete is not None:
        graph = remove_edges(graph, osm_ways_to_delete)

    return __setup_maxspeed(graph)


def __setup_maxspeed(graph,
                     motorway=80,
                     trunk=80,
                     motorway_link=60,
                     primary=50,
                     secondary=50,
                     tertiary=40,
                     residential=30):
    """ Add the maxspeed to the edges
    Args:
        graph: The graph to add the maxspeed
        motorway: The maxspeed for the motorway
        trunk: The maxspeed for the trunk
        motorway_link: The maxspeed for the motorway link
        primary: The maxspeed for the primary
        secondary: The maxspeed for the secondary
        tertiary: The maxspeed for the tertiary
        residential: The maxspeed for the residential
    Returns:
        The graph with the maxspeed added"""

    # Set the graph attributes I want as 'NaN' so there is no problem when plotting
    for u, v, data in graph.edges(data=True):

        if 'maxspeed' not in data:
            if data['highway'] == 'motorway':
                data['maxspeed'] = motorway
            elif data['highway'] == 'trunk':
                data['maxspeed'] = trunk
            elif data['highway'] == 'motorway_link':
                data['maxspeed'] = motorway_link
            elif data['highway'] == 'primary':
                data['maxspeed'] = primary
            elif data['highway'] == 'secondary':
                data['maxspeed'] = secondary
            elif data['highway'] == 'tertiary':
                data['maxspeed'] = tertiary
            elif data['highway'] == 'residential':
                data['maxspeed'] = residential
            else:
                data['maxspeed'] = None

    return graph


def add_traffic_level_from_file(graph, datafile, filename, neighbours_dictionary=None, fill_empty_edges=True,
                                precision=6):
    """ Add the traffic level to the edges from a file, and add the traffic level to the edges that are empty
    Args:
        graph: The graph to add the traffic level
        datafile: The file with the traffic level
        filename: The filename of the file
        fill_empty_edges: A boolean to indicate if the empty edges should be filled
        neighbours_dictionary: The dictionary with the neighbours of the edges
        precision: The precision to check the traffic level of the interpolations
    Returns:
        The graph with the traffic level added"""

    for u, v, edge_data in graph.edges(data=True):
        info = {'traffic_level': None, 'api_data': False}
        edge_data["dates"][filename] = info

    data = geojson.load(datafile)

    middle_coordinates_lat = []
    middle_coordinates_lon = []

    coordinates_lat = []
    coordinates_lon = []

    i = 0

    # Get from every feature (pair of points) the middle point
    for feature in data["features"]:

        if skip_feature(feature):
            continue

        i += 1
        coordinates = feature["geometry"]["coordinates"]

        # Get the two points of the edge
        point_1 = (coordinates[0][1], coordinates[0][0])
        point_2 = (coordinates[1][1], coordinates[1][0])

        # We will need this coordinates to get the bearing of the edge
        coordinates_lon.append(point_1[1])
        coordinates_lon.append(point_2[1])

        coordinates_lat.append(point_1[0])
        coordinates_lat.append(point_2[0])

        # Get the middle of both points to try to find the nearest edge in the graph
        middle_point = ((point_1[0] + point_2[0]) / 2, (point_1[1] + point_2[1]) / 2)
        middle_coordinates_lon.append(middle_point[1])
        middle_coordinates_lat.append(middle_point[0])

    # Get the list with the nearest edges and the distance to them
    nearest_edges_and_distance_list = ox.distance.nearest_edges(graph, middle_coordinates_lon, middle_coordinates_lat,
                                                                return_dist=True)

    if len(nearest_edges_and_distance_list[0]) != i:
        raise ValueError("ERROR: Different number of features and nearest edges")

    nearest_edges_list = nearest_edges_and_distance_list[0]
    nearest_distance_list = nearest_edges_and_distance_list[1]

    # Iteration over the features (easiest way to keep the order)
    j = 0
    for feature in data["features"]:
        if skip_feature(feature):
            continue

        info = {'traffic_level': feature["properties"]["traffic_level"], 'api_data': True}

        nearest_edge_id = nearest_edges_list[j]

        # We assume that the nearest edge is the correct one (reversed or not)
        node_1_id = nearest_edge_id[0]
        node_2_id = nearest_edge_id[1]
        nearest_edge = graph.edges[node_1_id, node_2_id, 0]

        # Then, we check if the road is reversed, if so, we invert the order of the edge's nodes
        bearing_api_edge = ox.bearing.calculate_bearing(coordinates_lat[j * 2], coordinates_lon[j * 2],
                                                        coordinates_lat[j * 2 + 1], coordinates_lon[j * 2 + 1])

        if not nearest_edge["oneway"] and are_opposite_bearings(nearest_edge["bearing"], bearing_api_edge):
            nearest_edge = graph.edges[node_2_id, node_1_id, 0]

        # Handle Jimenez Fraud Way (API edge is reversed)
        if (nearest_edge["osmid"] == 199419587
                and are_opposite_bearings(nearest_edge["bearing"], bearing_api_edge)):

            nearest_edge = __handle_jimenez_fraud(graph, node_1_id, node_2_id, filename, info)

        # Add traffic level
        nearest_edge["dates"][filename] = info

        j += 1

    if fill_empty_edges:
        interpolate_traffic_level(graph, filename, neighbours_dictionary=neighbours_dictionary, precision=precision)

    return graph


def __handle_jimenez_fraud(graph, node_1_id, node_2_id, filename, info):
    nearest_edge = graph.edges[node_1_id, node_2_id, 0]

    if node_1_id == 2094195157 and node_2_id == 2094195159:
        nearest_edge = graph.edges[418336300, 418336304, 0]
        extra_edge_info = graph.edges[418336304, 418336308, 0]
        extra_edge_info["dates"][filename] = info

    if node_1_id == 2094195165 and node_2_id == 3152120576:
        nearest_edge = graph.edges[418336289, 4943984606, 0]

        extra_edge_info = graph.edges[4943984604, 3152120577, 0]
        extra_edge_info["dates"][filename] = info

        extra_edge_info = graph.edges[3152120577, 418336292, 0]
        extra_edge_info["dates"][filename] = info

    if node_1_id == 2094195153 and node_2_id == 2094195155:
        nearest_edge = graph.edges[418336308, 2094195150, 0]

    if node_1_id == 2614757891 and node_2_id == 2094195161:
        nearest_edge = graph.edges[250962361, 2614757893, 0]

        extra_edge_info = graph.edges[2614757893, 5625095808, 0]
        extra_edge_info["dates"][filename] = info

        extra_edge_info = graph.edges[5625095808, 418336300, 0]
        extra_edge_info["dates"][filename] = info

    if node_1_id == 2094195161 and node_2_id == 2874546302:
        nearest_edge = graph.edges[2874546303, 250962361, 0]

    return nearest_edge


def get_connected_edges(graph, node1, node2):
    connected_edges = {}

    for edge in graph.neighbors(node1):
        if edge != node2:
            edge_data = graph[node1][edge][0]
            connected_edges[(node1, edge)] = edge_data

    for edge in graph.neighbors(node2):
        if edge != node1:
            edge_data = graph[node2][edge][0]
            connected_edges[(node2, edge)] = edge_data

    return connected_edges


def get_neighbours_edges(graph, node1, node2):
    """ Get the neighbours edges of the nodes
    Args:
        graph: The graph to get the neighbours edges
        node1: The first node
        node2: The second node"""
    neighbours_edges = []

    for u, v, data in graph.edges(data=True):
        if u == node1 or v == node1 or u == node2 or v == node2:
            neighbours_edges.append((u, v))

    neighbours_edges.remove((node1, node2))

    try:
        # Don't consider the reverse way of the edge, if it exists
        neighbours_edges.remove((node2, node1))
    except ValueError:
        pass

    return neighbours_edges


def interpolate_traffic_level(graph, filename, neighbours_dictionary=None, precision=6):
    """ Interpolate the traffic level of the edges with the traffic level of the neighbours that have it
    Args:
        graph: The graph to interpolate the traffic level
        filename: The filename of the date to interpolate
        precision: The precision to check the traffic level of the interpolations
        neighbours_dictionary: The dictionary with the neighbours of the edges"""

    num_iter = 0
    num_edges_interpolated = 1

    if neighbours_dictionary is None:
        print("Getting the neighbours edges...")
        d = {}
        for u, v, data in graph.edges(data=True):
            d[(u, v)] = get_neighbours_edges(graph, u, v)
    else:
        d = neighbours_dictionary

    print("Interpolating the traffic level...")
    while num_edges_interpolated > 0:
        num_edges_interpolated = 0
        num_iter += 1

        for u, v, data in graph.edges(data=True):
            if not data['dates'][filename]['api_data']:
                neighbours_edges = d[(u, v)]

                neighbour_traffic_levels = [graph.edges[edge[0], edge[1], 0]['dates'][filename]['traffic_level'] for
                                            edge in
                                            neighbours_edges if
                                            graph.edges[edge[0], edge[1], 0]['dates'][filename][
                                                'traffic_level'] is not None]

                if len(neighbour_traffic_levels) > 0:
                    new_traffic_level = sum(neighbour_traffic_levels) / len(neighbour_traffic_levels)

                    if round(new_traffic_level, precision) != round(
                            data['dates'][filename].get('traffic_level', -1) if data['dates'][filename].get(
                                'traffic_level', -1) is not None else -1,
                            precision):
                        data['dates'][filename]['traffic_level'] = new_traffic_level
                        num_edges_interpolated += 1

        if num_iter % 50 == 0:
            print("\tIteration: ", num_iter, " - Interpolated ", num_edges_interpolated, " edges\t\tfile =", filename)


def plot_graph_date_filename(graph, filename, size=6):
    """ Plot the graph by the traffic level attribute of the edges from a specific date (filename)
    Args:
        graph: The graph to plot
        filename: The filename of the date to plot
        size: The size of the plot"""

    for u, v, data in graph.edges(data=True):
        data['traffic_level'] = data['dates'][filename]['traffic_level']

    ec = ox.plot.get_edge_colors_by_attr(graph, 'traffic_level', cmap='RdYlGn', na_color='purple')
    ox.plot_graph(graph, edge_color=ec, node_color='w', node_edgecolor='k', figsize=(size, size))
    plt.show()


def save_graph(graph, filename):
    """ Save the graph to a file
    Args:
        graph: The graph to save
        filename: The filename to save the graph"""

    ox.save_graphml(graph, f"{filename}.graphml")


def add_traffic_level_from_folder(graph, folder, precision=6):
    """ Add the traffic level to the edges from a folder
    Args:
        graph: The graph to add the traffic level
        folder: The folder with the traffic level
        precision: The precision to check the traffic level of the interpolations
    Returns:
        The graph with the traffic level added"""

    print("Getting the neighbours edges dictionary...")
    neighbours_dictionary = {}
    for u, v, data in graph.edges(data=True):
        neighbours_dictionary[(u, v)] = get_neighbours_edges(graph, u, v)

    for filename in os.listdir(f"{folder}"):
        with open(f"{folder}/{filename}") as datafile:
            graph = add_traffic_level_from_file(graph, datafile, filename,
                                                neighbours_dictionary=neighbours_dictionary,
                                                precision=precision)
            print(f"Added traffic level from {filename}\n\n")

    return graph


if __name__ == "__main__":
    print("Running 'graph_functions.py' as main file.\n")
    # Example of use

    # Load the graph
    G = init_graph_bbox(constants.GRAPH_BBOX_NORTH, constants.GRAPH_BBOX_SOUTH,
                        constants.GRAPH_BBOX_EAST, constants.GRAPH_BBOX_WEST)

    # Add the traffic level from a file

    # with open("../output_split/mixed/2024_05_14_08_27_17.pbf.json") as file:
    #     G = add_traffic_level_from_file(G, file, "2024_05_14_08_27_17.pbf.json", precision=4)
    # plot_graph_date_filename(G, "2024_05_14_08_27_17.pbf.json", size=30)

    # Add the traffic level from a folder

    dir_input = "output_split/mixed"
    add_traffic_level_from_folder(G, dir_input, precision=4)
    print(json.dumps(list(G.edges(data=True))[7][2], indent=4))

    save_graph(G, "graph_output/graph_with_traffic_level_15files")
