import osmnx
import osmnx as ox
import networkx as nx
from mesa import Model
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
from traffic_model.agent import Car
from traffic_model.constants import POIs, EXIT_NODES, ENTRY_NODES
import logging

from traffic_model.model_get_data import compute_avg_travel_time, compute_avg_waiting_time, compute_avg_traffic_level, \
    compute_total_waiting_time, compute_total_travel_time, compute_avg_additional_time_in_route, compute_traffic_levels

# Configure loggers
logging.basicConfig(level=logging.INFO)

routing_logger = logging.getLogger('routing')


def get_graph(graphml_file):
    graph = ox.load_graphml(graphml_file)
    # Important to convert the traffic level to float, because default osmnx method converts it to string
    for edge in graph.edges(data=True):
        edge[2]["traffic_level"] = float(edge[2].get("traffic_level"))
        edge[2]["weight"] = float(1 + (1 - edge[2].get("traffic_level")))

    return graph


class TrafficModel(Model):
    def __init__(self, graphml_file, num_agents=10, start='random', end='random', respawn=True, routing='random'):
        super().__init__()
        self.graph = get_graph(graphml_file)
        self.schedule = RandomActivation(self)
        self.grid = NetworkGrid(self.graph)

        # Split the traffic level from the graph to be able to modify it easily
        self.traffic_level = {}

        # Handle MultiGraph cases
        if isinstance(self.graph, nx.MultiGraph):
            for u, v, key in self.graph.edges(keys=True):
                self.traffic_level[(u, v, key)] = float(self.graph.edges[u, v, 0].get("traffic_level", 0))

        else:
            for u, v in self.graph.edges:
                self.traffic_level[(u, v)] = float(self.graph.edges[u, v].get("traffic_level", 0))

        # Data collector will be executed at the end of each step
        self.datacollector = DataCollector(
            model_reporters={
                "AvgTravelTime": compute_avg_travel_time,
                "AvgWaitingTime": compute_avg_waiting_time,
                "AvgTrafficLevel": compute_avg_traffic_level,
                "TotalWaitingTime": compute_total_waiting_time,
                "TotalTravelTime": compute_total_travel_time,
                "AvgAdditionalTimeInRoute": compute_avg_additional_time_in_route,
                "TrafficLevels": compute_traffic_levels
            },
            agent_reporters={
                "TravelTime": "travel_time",
                "WaitingTime": "waiting_time",
                "AdditionalTimeInRoute": "additional_time_in_route"
            }
        )

        self.initialize_agents(num_agents, start, end, respawn, routing)

    def initialize_agents(self, num_agents, start_method, end_method, respawn_enabled, routing_method):
        for i in range(num_agents):
            start_node = self.get_start_node(start_method)

            x = 1
            while True:

                end_node = self.get_end_node(end_method)
                if nx.has_path(self.graph, start_node, end_node):
                    route = self.get_route(start_node, end_node, routing_method)

                    if len(route) - 1 >= 5 or routing_method == 'random':
                        if routing_method == 'weight_step':
                            agent = Car(i, self, route, start_method, end_method, respawn_enabled, routing_method,
                                        start_node, end_node)
                        else:
                            agent = Car(i, self, route, start_method, end_method, respawn_enabled, routing_method,
                                        start_node, end_node)

                        self.schedule.add(agent)
                        self.grid.place_agent(agent, start_node)
                        routing_logger.info(f"Agent {i} needs {x} tries to find a valid route")
                        break
                x += 1
                if x > 10:
                    routing_logger.info(
                        f"Agent {i} needs more than 10 tries to find a valid route, {start_node}, change start node")
                    start_node = self.get_start_node(start_method)

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()

    def get_end_node(self, end_method):
        if end_method == 'random':
            return self.random.choice(list(self.graph.nodes))
        elif end_method == 'pois':
            return self.random.choice(POIs)
        elif end_method == 'entry_exit':
            return self.random.choice(EXIT_NODES)

    def get_start_node(self, start_method):
        if start_method == 'random':
            return self.random.choice(list(self.graph.nodes))
        elif start_method == 'pois':
            return self.random.choice(POIs)
        elif start_method == 'entry_exit':
            return self.random.choice(ENTRY_NODES)

    def get_route(self, start_node, end_node, routing_method):
        """ Returns a route from start_node to end_node using the routing_method specified,
        which could be:
        'random'        ->  The movements will be random, without any routing
        'no_weight'     ->  The movements will be based on the shortest path, without considering the traffic level
        'weight_start'  ->  The movements will be based on the shortest path, considering the traffic level of the start
                            node
        'weight_step'   ->  The movements will be based on the shortest path, considering the traffic level and
                            calculating the traffic level of each step """

        if routing_method == 'no_weight':
            return list(nx.dijkstra_path(self.graph, source=start_node, target=end_node))
        elif routing_method == 'weight_start' or routing_method == 'weight_step':
            # if the routing method is 'weight_step' the route will be discarded in each step, but it's needed for the
            # agent to know the route in advance to ensure that the agent will reach the end node
            return list(nx.dijkstra_path(self.graph, source=start_node, target=end_node, weight='weight'))
        else:
            return [start_node]
