from collections import defaultdict
import json
import os


def count_all_files_unique_pairs(dirname, print_information=False):
    """ Count all the unique pairs of coordinates in all the files in the given directory

        Args:
            dirname: The directory where the files are located
            print: If True, print the number of unique pairs, repeated pairs and files
        Returns:
            A list with the number of unique pairs, the number of repeated pairs and the number of files"""

    dictionary = defaultdict(int)
    number_of_files = 0
    # Open each file in the "./json_data" folder
    for filename in os.listdir(dirname):

        if print_information:
            print(filename)

        with open(f"./{dirname}/{filename}") as file:
            current_number_of_lines = len(dictionary)
            number_of_files += 1
            json_coordinates = json.load(file)
            for feature in json_coordinates["features"]:
                coordinates = feature["geometry"]["coordinates"]

                # Skip points
                if feature["geometry"]["type"] == "Point":
                    continue

                for line in coordinates:
                    for point_number in range(len(line) - 1):
                        next_pair = [line[point_number], line[point_number + 1]]
                        dictionary[str(next_pair)] += 1

        # Check how many new lines are added
        next_number_of_lines = len(dictionary)

        if print_information:
            print(f"\t New {next_number_of_lines - current_number_of_lines} unique pairs added")

    # print(json.dumps(translation))

    repeated_pairs = 0
    unique_pairs = 0
    for x, y in dictionary.items():
        if y > 1:
            repeated_pairs += 1
        else:
            unique_pairs += 1

    return unique_pairs, repeated_pairs, number_of_files


def count_all_files_unique_lines(dirname, print_information=False):
    """ Count all the unique lines of coordinates in all the files in the given directory

        Args:
            dirname: The directory where the files are located
            print: If True, print the number of unique lines, repeated lines and files
        Returns:
            A list with the number of unique lines, the number of repeated lines and the number of files"""

    dict = defaultdict(int)
    number_of_files = 0
    # Open each file in the "./json_data" folder
    for filename in os.listdir(dirname):

        if print_information:
            print(filename)

        with open(f"./{dirname}/{filename}") as file:
            current_number_of_lines = len(dict)
            number_of_files += 1
            json_coordinates = json.load(file)
            for feature in json_coordinates["features"]:
                coordinates = feature["geometry"]["coordinates"]

                # Skip points
                if feature["geometry"]["type"] == "Point":
                    continue

                for line in coordinates:
                    next_line = []
                    for point in line:
                        next_line.append([
                            point[0], point[1]
                        ])
                    dict[str(next_line)] += 1

        # Check how many new lines are added
        next_number_of_lines = len(dict)

        if print_information:
            print(f"\t New {next_number_of_lines - current_number_of_lines} unique lines added")

    repeated_lines = 0
    unique_lines = 0
    for x, y in dict.items():
        if y > 1:
            repeated_lines += 1
        else:
            unique_lines += 1

    return unique_lines, repeated_lines, number_of_files


def count_edges_with_length(graph, threshold=5):
    """ Count the number of edges in the graph with a length less than the given threshold

        Args:
            graph: The graph to check
            threshold: The maximum length of the edges
        Returns:
            The number of edges with a length less than the threshold"""

    # Check how many edges are less than X meters long
    # Initialize counters
    longer_than_threshold = []
    shorter_than_threshold = []

    edge_data_list = list(graph.edges(data=True))
    for (edge, _, data) in edge_data_list:
        edge_length = data['length']
        if edge_length < threshold:
            shorter_than_threshold.append(edge_length)
        else:
            longer_than_threshold.append(edge_length)

    # Example value for comparison

    print("Number of elements longer than", threshold, ":", len(longer_than_threshold))
    print("Number of elements shorter than", threshold, ":", len(shorter_than_threshold))


if __name__ == "__main__":
    print("Running 'stats.py' as main file.\n")

    directory = "../output_pairs/tile1"

    up, rp, nf = count_all_files_unique_pairs(directory, print_information=False)
    print(f"Unique pairs: {up}")
    print(f"Repeated pairs: {rp}")
    print(f"Number of files: {nf}\n")

    # You cant count lines in a split by pairs file
    directory = "../json_data"

    up, rp, nf = count_all_files_unique_lines(directory, print_information=False)
    print(f"Unique lines: {up}")
    print(f"Repeated lines: {rp}")
    print(f"Number of lines: {nf}\n")
