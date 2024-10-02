import copy
import os

from shapely.geometry import LineString, Point
import shapely
import geojson

from mapfunctions.utils import skip_feature


def split_features(geojson_file,
                   print_if_more_splits_than=-1):
    data = geojson.load(geojson_file)
    new_features = []
    # Split the features
    for feature in data['features']:
        if skip_feature(feature):
            continue

        # Split each feature into segments
        amount_of_splits = feature['properties']['splits']

        if amount_of_splits < 2:
            new_features.append(feature)
            continue
        else:

            if 0 < print_if_more_splits_than < amount_of_splits:
                print("More than 10 splits -> ", amount_of_splits)

            # Get the coordinates of the original feature
            coordinates = feature['geometry']['coordinates']
            line = LineString(coordinates)

            geometries = split_line_with_two_points_in_parts(line, amount_of_splits, format_geojson=False)

            for geometry in geometries:
                # Get the properties of the original feature
                new_feature = copy.deepcopy(feature)
                new_feature['geometry'] = geometry
                new_feature['properties']['splits'] = -1

                new_features.append(new_feature)

    data['features'] = new_features
    return data


# Function to split the line in the argument given parts
def split_line_with_two_points_in_parts(line, parts, format_geojson=False):
    # Check if the argument is LineString
    if not isinstance(line, LineString):
        raise ValueError("Input line should be a shapely LineString")

    # Check if the line has two points
    if len(list(line.coords)) != 2:
        raise ValueError("Line should have two points")

    coords = list(line.coords)
    first_point = Point(coords[0])
    last_point = Point(coords[1])

    line_length = line.length

    # Get the step to split the line
    step = line_length / parts

    # Initialize the list of the new lines
    current_step = 0

    # Initialize the current line
    current_line = [first_point]

    # Iterate over the line
    while current_step + step < line_length:
        # Get the point in the current step
        new_point = line.interpolate(current_step + step)
        # Add the point to the current line
        current_line.append(new_point)
        # Update the current step
        current_step += step

    # Add the last point of the line
    current_line.append(last_point)

    # Split the line into lines with two points
    pairs_points_lines = []
    for i in range(len(current_line) - 1):
        pairs_points_lines.append((LineString([current_line[i], current_line[i + 1]])))

    if format_geojson:
        # print([shapely.to_geojson(line) for line in pairs_points_lines])
        return [shapely.to_geojson(line) for line in pairs_points_lines]

    return pairs_points_lines


def split_features_from_folder(folder_input, folder_output):
    # Read the files in the folder
    for filename in os.listdir(f"{folder_input}"):
        with open(f"{folder_input}/{filename}") as f:
            split_data = split_features(f)

        with open(f"{folder_output}/{filename}", "w") as output_file:
            geojson.dump(split_data, output_file)

        print(f"File '{filename}' splitted and saved on '{folder_output}'")


if __name__ == "__main__":
    print("Running 'split.py' as main file.\n")

    folder_i = "output_add_info/mixed"
    folder_o = "output_split/mixed"

    # file_n = "2024_05_14_08_27_17.pbf.json"
    # with open(f"../{folder_i}/{file_n}") as f:
    #     split_data = split_features(f)

    split_features_from_folder(folder_i, folder_o)
