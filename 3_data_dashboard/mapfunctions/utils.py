import math


def get_geojson_corners_coordinates(x_tile, y_tile, zoom, format="latlng"):
    """ Get the coordinates of the corners of a tile in the GeoJSON format
    Args:
        x_tile: The x coordinate of the tile
        y_tile: The y coordinate of the tile
        zoom: The zoom level of the tile
        format: The format of the coordinates. Choose between 'latlng' and 'lnglat'
    Returns:
         A list with the coordinates of the corners of the tile in the GeoJSON format"""

    lng_left = x_tile * 360 / (2 ** zoom) - 180
    lng_right = (x_tile + 1) * 360 / (2 ** zoom) - 180
    lat_top = math.atan(math.sinh(math.pi * (1 - 2 * y_tile / (2 ** zoom)))) * 180 / math.pi
    lat_bottom = math.atan(math.sinh(math.pi * (1 - 2 * (y_tile + 1) / (2 ** zoom)))) * 180 / math.pi

    if format == "latlng":
        return [
            [lat_top, lng_left],
            [lat_bottom, lng_left],
            [lat_bottom, lng_right],
            [lat_top, lng_right],
            [lat_top, lng_left]  # Closing coordinate
        ]
    elif format == "lnglat":
        return [
            [lng_left, lat_top],
            [lng_left, lat_bottom],
            [lng_right, lat_bottom],
            [lng_right, lat_top],
            [lng_left, lat_top]  # Closing coordinate
        ]
    else:
        raise ValueError("Invalid format. Choose 'latlng' or 'lnglat'.")


def normalize(x, in_min, in_max, out_min, out_max):
    """ Normalize a value from one range to another
    Args:
        x: The value to normalize
        in_min: The minimum value of the input range
        in_max: The maximum value of the input range
        out_min: The minimum value of the output range
        out_max: The maximum value of the output range
    Returns:
        The normalized value"""

    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def float_to_hex_color(value, dashboard_output=False):
    """
    Convert a float between 0 and 1 to a hex color representing traffic flow density.
    0 = Red (worst case)
    0.5 = Orange (moderate case)
    1 = Green (best case)
    """
    # Clamp the value to the range [0, 1]
    value = max(0, min(1, value))

    # Define the RGB values for red, orange, and green
    red = (255, 0, 0)
    orange = (255, 165, 0)
    green = (0, 255, 0)

    if value < 0.5:
        # Interpolate between red and orange
        ratio = value / 0.5
        r = int(red[0] + ratio * (orange[0] - red[0]))
        g = int(red[1] + ratio * (orange[1] - red[1]))
        b = int(red[2] + ratio * (orange[2] - red[2]))
    else:
        # Interpolate between orange and green
        ratio = (value - 0.5) / 0.5
        r = int(orange[0] + ratio * (green[0] - orange[0]))
        g = int(orange[1] + ratio * (green[1] - orange[1]))
        b = int(orange[2] + ratio * (green[2] - orange[2]))

    # Convert the RGB values to a hex string
    if dashboard_output:
        hex_color = f'{r:02X}{g:02X}{b:02X}'
    else:
        hex_color = f'#{r:02X}{g:02X}{b:02X}'
    return hex_color


def are_opposite_bearings(bearing_1, bearing_2, tolerance=45):
    """ Check if two bearings are opposite to each other
    Args:
        bearing_1: The first bearing
        bearing_2: The second bearing
        tolerance: The maximum difference between the bearings to consider them opposite
    Returns:
        A boolean indicating if the bearings are opposite"""

    return abs(bearing_1 - bearing_2) > 180 - tolerance


def get_cardinal_direction_from_bearing(bearing):
    """ Get the cardinal direction from a bearing
    Args:
        bearing: The bearing in degrees
    Returns:
        A string with the cardinal direction"""

    points = ["north", "north east", "east", "south east", "south", "south west", "west", "north west"]

    bearing = bearing % 360
    bearing = int(bearing / 45)  # values 0 to 7
    return points[bearing]


def skip_feature(feature):
    """ Check if the feature should be skipped
    Args:
        feature: The feature to check
    Returns:
        A boolean indicating if the feature should be skipped"""

    if "geometry" not in feature.keys():
        return True
    if "coordinates" not in feature["geometry"].keys():
        return True
    if len(feature["geometry"]["coordinates"]) != 2:
        return True

    return False


if __name__ == "__main__":
    print("Running 'utils.py' as main file.\n")

    x_tile_coords = 7988
    y_tile_coords = 6393
    zoom = 14

    geojson_coordinates_tile1 = get_geojson_corners_coordinates(x_tile_coords, y_tile_coords, zoom, format="lnglat")
    print(geojson_coordinates_tile1)
    geojson_coordinates_tile2 = get_geojson_corners_coordinates(x_tile_coords, y_tile_coords - 1, zoom, format="lnglat")
    print(geojson_coordinates_tile2)
