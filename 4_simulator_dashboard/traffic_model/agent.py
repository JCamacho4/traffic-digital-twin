import networkx as nx
from mesa import Agent
import logging

# Define custom loggers
movement_logger = logging.getLogger('movement')
respawning_logger = logging.getLogger('respawning')
waiting_logger = logging.getLogger('waiting')


class Car(Agent):
    def __init__(self, unique_id, model, route, start_method, end_method, respawn_enabled, routing_method, start_node,
                 end_node=None, graph=None):
        super().__init__(unique_id, model)
        self.route = route
        self.current_step = 0
        self.travel_time = 0
        # Waiting time is the time that the agent has been waiting in the same edge (not moving)
        self.waiting_time = 0
        # Additional time in route is the time that the agent has seen its route slowed down by traffic
        self.additional_time_in_route = 0

        # This will be useful to generate the same type of agent if it can respawn
        self.start_method = start_method
        self.end_method = end_method
        self.routing_method = routing_method
        self.respawn_enabled = respawn_enabled

        # Define the Car location
        self.previous_node = None
        self.start_node = start_node
        self.current_node = start_node
        self.end_node = end_node

        # Another way to define the Car location
        self.current_node = self.route[0] if self.route else None
        self.previous_node = None


    def step(self):
        if self.routing_method == 'no_weight' or self.routing_method == 'weight_start':
            self.follow_route()
        elif self.routing_method == 'random':
            self.random_move()
        elif self.routing_method == 'weight_step':
            self.next_movement_by_weight()

        self.travel_time += 1

    def follow_route(self):
        current_edge = (self.previous_node, self.current_node, 0) if self.previous_node else None
        if self.current_node != self.end_node:
            next_node = self.route[self.current_step + 1]
            next_edge = (self.current_node, next_node, 0)

            self.handle_movement(current_edge, next_edge, next_node)
        else:
            self.handle_stop_respawn(current_edge)

    def next_movement_by_weight(self):
        current_edge = (self.previous_node, self.current_node, 0) if self.previous_node else None
        if self.current_node != self.end_node:
            path = nx.dijkstra_path(self.model.graph, source=self.current_node, target=self.end_node, weight='weight')

            # The next node is the second element of the path, because the first one is the current node
            next_node = path[1]
            next_edge = (self.current_node, next_node, 0)

            self.handle_movement(current_edge, next_edge, next_node)
        else:
            self.handle_stop_respawn(current_edge)

    def random_move(self):
        if isinstance(self.model.graph, nx.MultiGraph):
            possible_moves = [(u, v, key) for u, v, key in self.model.graph.edges(self.current_node, keys=True) if
                              self.model.traffic_level[(u, v, key)] >= 0]
        else:
            possible_moves = [(u, v) for u, v in self.model.graph.edges(self.current_node) if
                              self.model.traffic_level[(u, v)] >= 0]

        current_edge = (self.previous_node, self.current_node, 0) if self.previous_node else None

        if possible_moves:
            next_edge = self.random.choice(possible_moves)
            next_node = next_edge[1]

            self.handle_movement(current_edge, next_edge, next_node)
        else:
            self.handle_stop_respawn(current_edge)

    def handle_movement(self, current_edge, next_edge, next_node):
        if self.model.traffic_level[next_edge] > 0:
            self.current_step += 1

            if current_edge:
                if self.model.traffic_level[current_edge] <= 0.9:
                    self.model.traffic_level[current_edge] += 0.1
                else:
                    self.model.traffic_level[current_edge] = 1

                self.model.graph.edges[current_edge]['weight'] = 1 + (1 - self.model.traffic_level[current_edge])



            if self.model.traffic_level[next_edge] >= 0.1:
                self.model.traffic_level[next_edge] -= 0.1
            else:
                self.model.traffic_level[next_edge] = 0

            self.model.graph.edges[next_edge]['weight'] = 1 + (1 - self.model.traffic_level[next_edge])

            # Add additional time in route if the agent is slowed down by traffic
            self.additional_time_in_route += 1 - self.model.traffic_level[next_edge]

            # Move to the next node
            self.previous_node = self.current_node
            self.current_node = next_node
            self.model.grid.move_agent(self, next_node)
            movement_logger.info(
                f"Car {self.unique_id} moved from {self.previous_node} to {self.current_node}")
        else:
            self.waiting_time += 1
            waiting_logger.info(
                f"Car {self.unique_id} waiting at {self.current_node}, in the step {self.current_step}")

    def handle_stop_respawn(self, current_edge):
        # Update the traffic level of the current edge before removing the agent
        if current_edge:
            if self.model.traffic_level[current_edge] <= 0.9:
                self.model.traffic_level[current_edge] += 0.1
            else:
                self.model.traffic_level[current_edge] = 1

        self.model.schedule.remove(self)

        if self.respawn_enabled:
            # Respawn an agent with the same characteristics
            self.model.initialize_agents(1,
                                         self.start_method,
                                         self.end_method,
                                         self.respawn_enabled,
                                         self.routing_method)

            respawning_logger.info(f"Car {self.unique_id} has reached a final node, "
                                   f"respawning a new agent")
