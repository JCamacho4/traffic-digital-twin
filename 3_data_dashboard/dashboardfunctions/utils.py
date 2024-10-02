from dash_sylvereye.defaults import get_default_node_options, get_default_edge_options
from dash_sylvereye.enums import EdgeColorMethod
import osmnx as ox

from dash_sylvereye.utils import load_from_osmnx_graph
from dashboardfunctions.color import color_by_attribute


def get_node_edge_options():
    node_options = get_default_node_options()
    node_options["alpha_default"] = 1
    node_options["size_default"] = 0.0001
    node_options["color_default"] = 0x000000

    # set visual options for edges
    edge_options = get_default_edge_options()
    edge_options["width_default"] = 0.05
    edge_options["alpha_default"] = 1
    edge_options["color_method"] = EdgeColorMethod.CUSTOM

    return node_options, edge_options


def get_road_data_from_graph_with_dictionary(graph_location):
    road_network = ox.load_graphml(graph_location)
    data_date = '2024_05_14_08_57_19.pbf.json'

    nodes_data, edges_data = load_from_osmnx_graph(road_network, data_date)

    color_by_attribute(edges_data)

    return nodes_data, edges_data, road_network


def get_road_data_from_graph(graph):
    nodes_data, edges_data = load_from_osmnx_graph(graph)

    color_by_attribute(edges_data)

    return nodes_data, edges_data


def get_marks_each_60_minutes_with_half_hour_marks():
    dictionary = {}
    hour = 0
    minute = 0
    interval = 0.5  # 30 minutes

    for i in range(int(24 / interval)):  # Loop through the day in 30-minute intervals
        key = round(i * interval, 2)

        if key.is_integer():
            key = int(key)

        if minute == 0:
            dictionary[key] = {'label': f"{hour:02d}:{minute:02d}"}
        else:
            dictionary[key] = {'label': ''}

        minute += 30
        if minute == 60:
            minute = 0
            hour += 1

    return dictionary


def translate_float_array_to_hour_string(array):
    return [translate_from_float_to_time_string(time_float) for time_float in array]


def translate_from_float_to_time_string(time_float):
    hour = int(time_float)
    minutes = int((time_float - hour) * 60)

    return f"{hour:02d}:{minutes:02d}"


def add_info_from_mesa_list(edges_list_with_data, edges):
    print("Adding info from Mesa list")



# {'osmid': 359280372, 'current_speed': 39.47466081733532, 'api_data': False, 'traffic_level': 0.7894932163467063, 'source': 21497117, 'target': 21497131, 'key': 0}
# {'coords': [[36.7201549, -4.4601866], [36.7200901, -4.4603168]], 'visible': True, 'alpha': 1.0, 'width': 0.25, 'color': 0, 'data': {'access': None, 'bridge': None, 'geometry': None, 'highway': 'secondary', 'junction': 'roundabout', 'lanes': '3', 'length': 13.66, 'maxspeed': '50', 'name': 'Plaza Pintor Sandro Botticelli', 'oneway': True, 'osmid': 359280372, 'ref': None, 'service': None, 'source_osmid': 21497117, 'target_osmid': 21497131, 'traffic_level': None, 'current_speed': None, 'api_data': 'False', 'bearing': 238.2}}
def add_info_from_mongo_list(edges_list_with_data, edges, attribute='traffic_level'):
    traffic_level_dict = {
        (edge['source'], edge['target']): float(edge['traffic_level'])
        for edge in edges_list_with_data
    }

    current_speed_dict = {
        (edge['source'], edge['target']): float(edge['current_speed'])
        for edge in edges_list_with_data
    }

    api_data_dict = {
        (edge['source'], edge['target']): edge['api_data']
        for edge in edges_list_with_data
    }

    for edge in edges:
        source = edge['data']['source_osmid']
        target = edge['data']['target_osmid']
        if (source, target) in traffic_level_dict:
            edge['data']['traffic_level'] = traffic_level_dict[(source, target)]

        if (source, target) in current_speed_dict:
            edge['data']['current_speed'] = current_speed_dict[(source, target)]

        if (source, target) in api_data_dict:
            edge['data']['api_data'] = api_data_dict[(source, target)]

    return edges


def get_min_max_values_from_attribute_edges_data(edges_data, attribute="traffic_level"):
    min_val = 500.0
    max_val = 0.0

    if attribute == "traffic_level":
        min_val = 0.0
        max_val = 1.0
    else:
        for edge in edges_data:
            if (attribute in edge["data"]
                    and edge["data"][attribute] is not None
                    and edge["data"][attribute] != "None"):
                min_val = min(min_val, float(edge["data"][attribute]))
                max_val = max(max_val, float(edge["data"][attribute]))

    return min_val, max_val


if __name__ == "__main__":
    print("Running 'utils.py' as main file.\n")
