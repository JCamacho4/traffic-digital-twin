from traffic_model.model import TrafficModel
from traffic_model.mongo_connections import get_database, get_edges_by_filename
import logging

import osmnx as ox

from traffic_model.model_get_data import analyze_and_plot_simulation_data

# Configure loggers
logging.basicConfig(level=logging.INFO)

movement_logger = logging.getLogger('movement')
respawning_logger = logging.getLogger('respawning')
waiting_logger = logging.getLogger('waiting')
routing_logger = logging.getLogger('routing')


def configure_logging(enable_movement=False, enable_respawning=False, enable_waiting=False, enable_routing=False):
    if enable_movement:
        movement_logger.setLevel(logging.INFO)
    else:
        movement_logger.setLevel(logging.WARNING)

    if enable_respawning:
        respawning_logger.setLevel(logging.INFO)
    else:
        respawning_logger.setLevel(logging.WARNING)

    if enable_waiting:
        waiting_logger.setLevel(logging.INFO)
    else:
        waiting_logger.setLevel(logging.WARNING)

    if enable_routing:
        routing_logger.setLevel(logging.INFO)
    else:
        routing_logger.setLevel(logging.WARNING)


def set_traffic_level_graph(date):
    graph = ox.load_graphml('base_graph.graphml')

    db = get_database("TFG")
    edges = get_edges_by_filename(db, date)

    for edge in edges:
        graph.edges[edge['source'], edge['target'], 0]["traffic_level"] = float(edge['traffic_level'])
        # Inverse traffic level to be able to use it as a weight
        graph.edges[edge['source'], edge['target'], 0]["weight"] = float(1 + (1 - edge['traffic_level']))

    # save the graph with the traffic level
    saved_graph_name = 'graph_with_traffic.graphml'
    ox.save_graphml(graph, saved_graph_name)

    return saved_graph_name


def run_simulation(steps, num_agents, graph_filename, start='random', end='random', respawn=True, routing='random',
                   # Logging configuration
                   enable_movement=False, enable_respawning=False, enable_waiting=False, enable_routing=False,
                   progress_function=None, plot_ide=False):
    configure_logging(enable_movement, enable_respawning, enable_waiting, enable_routing)

    graph_filename = set_traffic_level_graph(graph_filename)
    model = TrafficModel(graph_filename,
                         num_agents=num_agents,
                         start=start,
                         end=end,
                         respawn=respawn,
                         routing=routing)

    print("Model initialized, starting simulation")
    each_percent = steps // 100
    if each_percent == 0:
        each_percent = 1
    current_percent = 0

    print("Simulation started")

    for i in range(steps):
        model.step()

        if progress_function is not None:
            progress_function((str(i), str(steps)))

        if i % each_percent == 0:
            current_percent += 2
            print(f"Step {i}")
            total_waiting_time = model.datacollector.get_model_vars_dataframe()['TotalWaitingTime'].iloc[-1]
            total_travel_time = model.datacollector.get_model_vars_dataframe()['TotalTravelTime'].iloc[-1]
            print(f"Current Waiting Time of the agents: {total_waiting_time}")
            print(f"Current Travel Time of the agents: {total_travel_time}")

    print("Simulation finished\n\n")

    # Get the graph with the traffic level after the simulation
    traffic_level_output = model.traffic_level

    # Retrieve and analyze the collected data
    model_data = model.datacollector.get_model_vars_dataframe()
    agent_data = model.datacollector.get_agent_vars_dataframe()

    if plot_ide:
        analyze_and_plot_simulation_data(model_data, agent_data)

    return traffic_level_output, model_data, agent_data


if __name__ == "__main__":
    # MAIN CHARACTERISTICS OF THE SIMULATION
    steps_number = 100
    agents_number = 100
    graph_datetime_filename = '2024_05_08_16_19_06.pbf.json'

    # CONFIGURE THE SIMULATION
    agents_start_method = 'random'  # 'random' // 'pois' // 'entry_exit' //TODO: incluir en función del tráfico ??
    agents_end_method = 'random'  # 'random' // 'pois' // 'entry_exit'
    respawn_enabled = True  # True // False
    routing_method = 'weight_start'  # 'random' // 'no_weight' // 'weight_start' // 'weight_step'

    # RUN THE SIMULATION
    simulation = run_simulation(steps_number,
                                agents_number,
                                graph_datetime_filename,
                                start=agents_start_method,
                                end=agents_end_method,
                                respawn=respawn_enabled,
                                routing=routing_method,
                                # Logging configuration
                                enable_movement=False,
                                enable_respawning=False,
                                enable_waiting=True,
                                enable_routing=False)
