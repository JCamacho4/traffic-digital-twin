

def float_to_hex_color(value, dashboard_output=False, min_val=0, max_val=1):
    """
    Convert a float between 0 and 1 to a hex color representing traffic flow density.
    0 = Red (worst case)
    0.5 = Orange (moderate case)
    1 = Green (best case)
    """

    # Normalize the value to the range [0, 1]
    if max_val != min_val:  # Prevent division by zero
        value = (value - min_val) / (max_val - min_val)
    else:
        value = 0  # If min_val equals max_val, set value to 0

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


def color_by_attribute(edges_data, attribute="traffic_level", min_val=0, max_val=1):
    for edge in edges_data:
        if ("traffic_level" in edge["data"]
                and edge["data"][attribute] is not None
                and edge["data"][attribute] != "None"):

            edge["color"] = int(
                float_to_hex_color(float(edge["data"][attribute]), dashboard_output=True, min_val=min_val, max_val=max_val),
                base=16)
        else:
            edge["color"] = 0x000000
