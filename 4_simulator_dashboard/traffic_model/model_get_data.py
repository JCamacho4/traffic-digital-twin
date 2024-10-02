import pandas as pd
import matplotlib.pyplot as plt


def analyze_and_plot_simulation_data(model_data, agent_data):
    print("===================== \n\n DATA ANALYSIS\n\n =====================\n\n")
    # Convert model_data and agent_data to DataFrames
    model_df = pd.DataFrame(model_data)
    agent_df = pd.DataFrame(agent_data)

    # Plot Average Travel Time over steps
    plt.figure(figsize=(12, 6))
    plt.plot(model_df.index, model_df["AvgTravelTime"], label="Average Travel Time")
    plt.xlabel("Step")
    plt.ylabel("Average Travel Time")
    plt.title("Average Travel Time over Steps")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Average Waiting Time over steps
    plt.figure(figsize=(12, 6))
    plt.plot(model_df.index, model_df["AvgWaitingTime"], label="Average Waiting Time")
    plt.xlabel("Step")
    plt.ylabel("Average Waiting Time")
    plt.title("Average Waiting Time over Steps")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Total Travel Time over steps
    plt.figure(figsize=(12, 6))
    plt.plot(model_df.index, model_df["TotalTravelTime"], label="Total Travel Time")
    plt.xlabel("Step")
    plt.ylabel("Total Travel Time")
    plt.title("Total Travel Time over Steps")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Total Waiting Time over steps
    plt.figure(figsize=(12, 6))
    plt.plot(model_df.index, model_df["TotalWaitingTime"], label="Total Waiting Time")
    plt.xlabel("Step")
    plt.ylabel("Total Waiting Time")
    plt.title("Total Waiting Time over Steps")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Average Additional Time in Route over steps
    plt.figure(figsize=(12, 6))
    plt.plot(model_df.index, model_df["AvgAdditionalTimeInRoute"], label="Average Additional Time in Route")
    plt.xlabel("Step")
    plt.ylabel("Average Additional Time in Route")
    plt.title("Average Additional Time in Route over Steps")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot Average Traffic Level over steps
    plt.figure(figsize=(12, 6))
    plt.plot(model_df.index, model_df["AvgTrafficLevel"], label="Average Traffic Level")
    plt.xlabel("Step")
    plt.ylabel("Average Traffic Level")
    plt.title("Average Traffic Level over Steps")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Histogram of Travel Times
    plt.figure(figsize=(12, 6))
    plt.hist(agent_df["TravelTime"], bins=30, edgecolor='k', alpha=0.7)
    plt.xlabel("Travel Time")
    plt.ylabel("Number of Agents")
    plt.title("Distribution of Travel Times")
    plt.grid(True)
    plt.show()

    # Histogram of Waiting Times
    plt.figure(figsize=(12, 6))
    plt.hist(agent_df["WaitingTime"], bins=30, edgecolor='k', alpha=0.7)
    plt.xlabel("Waiting Time")
    plt.ylabel("Number of Agents")
    plt.title("Distribution of Waiting Times")
    plt.grid(True)
    plt.show()

    # Print Summary Statistics
    print("Summary Statistics for Travel Times:")
    print(agent_df["TravelTime"].describe())

    print("\nSummary Statistics for Waiting Times:")
    print(agent_df["WaitingTime"].describe())

    print("\nSummary Statistics for Additional Time in Route:")
    print(agent_df["AdditionalTimeInRoute"].describe())

def compute_avg_travel_time(model):
    agent_travel_times = [agent.travel_time for agent in model.schedule.agents if agent.travel_time > 0]
    return sum(agent_travel_times) / len(agent_travel_times) if agent_travel_times else 0


def compute_avg_waiting_time(model):
    agent_waiting_times = [agent.waiting_time for agent in model.schedule.agents if agent.waiting_time > 0]
    return sum(agent_waiting_times) / len(agent_waiting_times) if agent_waiting_times else 0


def compute_total_waiting_time(model):
    return sum(agent.waiting_time for agent in model.schedule.agents)


def compute_total_travel_time(model):
    return sum(agent.travel_time for agent in model.schedule.agents)


def compute_avg_additional_time_in_route(model):
    agent_additional_times = [agent.additional_time_in_route for agent in model.schedule.agents if
                              agent.additional_time_in_route > 0]
    return sum(agent_additional_times) / len(agent_additional_times) if agent_additional_times else 0


def compute_avg_traffic_level(model):
    traffic_levels = model.traffic_level.values()
    return sum(traffic_levels) / len(traffic_levels) if traffic_levels else 0


def compute_traffic_levels(model):
    return dict(model.traffic_level)
