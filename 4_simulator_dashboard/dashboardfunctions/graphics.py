import math
import plotly.graph_objects as go

from dashboardfunctions.color import float_to_hex_color


def __add_single_arrow(fig, x1, y1, x2, y2, tl, line_width, min_val=0.0, max_val=1.0):
    if tl is None or tl >= 0:
        if tl is None:
            color = "#000000"
            name = "No data"
        elif tl >= 0:
            color = float_to_hex_color(tl, min_val=min_val, max_val=max_val)
            name = round(tl, 3)

        # Add the first line
        fig.add_trace(go.Scatter(x=[x1, x2], y=[y1, y2], mode='lines', line=dict(color=color, width=line_width),
                                 name=name))
        # Add arrow in the direction of bearing
        fig.add_annotation(
            x=x2, y=y2,  # Position of the arrow
            ax=x1, ay=y1,  # Starting point of the arrow
            xref='x', yref='y',
            axref='x', ayref='y',
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor=color  # Color of the arrow
        )


def create_arrows(bearing, tl_1=None, tl_2=-1, separation_factor=0.6, line_width=2, line_length=12, min_val=0.0,
                  max_val=1.0):
    # Increase the separation between the lines
    separation = line_length * separation_factor

    # Convert bearing from clockwise degrees to counterclockwise degrees
    bearing = (90 - bearing) % 360

    # Convert bearing from degrees to radians
    bearing_rad = math.radians(bearing)

    # Calculate the coordinates of the first line
    x1 = 0
    y1 = 0
    x2 = line_length * math.cos(bearing_rad)
    y2 = line_length * math.sin(bearing_rad)

    # Calculate the coordinates of the second line (parallel) with increased separation
    x3 = separation * math.cos(bearing_rad + math.pi / 2)
    y3 = separation * math.sin(bearing_rad + math.pi / 2)
    x4 = x2 + x3
    y4 = y2 + y3

    # Create a Plotly figure with equal aspect ratio
    fig = go.Figure()

    if tl_1 is None or tl_1 >= 0:
        __add_single_arrow(fig, x1, y1, x2, y2, tl_1, line_width, min_val=min_val, max_val=max_val)

    if tl_2 is None or tl_2 >= 0:
        __add_single_arrow(fig, x4, y4, x3, y3, tl_2, line_width, min_val=min_val, max_val=max_val)

    # Set axis titles
    fig.update_layout(xaxis_title="", yaxis_title="")

    # Set equal aspect ratio
    fig.update_layout(
        yaxis=dict(scaleanchor="x", scaleratio=1),
        xaxis=dict(scaleanchor="y", scaleratio=1)
    )

    fig.update_layout(xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))

    # Set background color to white (or any other color you prefer)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')  # Transparent background

    # Ensure the legend is always displayed
    fig.update_layout(showlegend=True)

    return fig


def create_horizontal_bars_by_name_graph(data, selected_category):
    if len(data) == 0:
        return go.Figure()  # Return an empty figure initially

    # Create the figure
    fig = go.Figure()

    for item in data:
        fig.add_trace(go.Bar(
            y=[item['_id']],
            x=[item[selected_category]],
            name=selected_category,
            orientation='h',
            showlegend=False
        ))

    # Update layout with autoscaling and more space for y-axis labels
    fig.update_layout(
        title=f'{selected_category} by Street',
        xaxis_title=selected_category,
        yaxis_title='Street',
        yaxis={'automargin': True},  # Enable automargin for y-axis
        margin=dict(l=150, r=80, t=50, b=50),  # Adjust margins for wider grid and space for additional info
        height=150 + 40 * len(data),
        xaxis=dict(side='top'),
        showlegend=False
    )

    return fig


def create_vertical_bars_by_hours_graph(data, selected_category):
    if len(data) == 0:
        return go.Figure()  # Return an empty figure initially

    # Create the figure
    fig = go.Figure()

    for item in data:
        fig.add_trace(go.Bar(
            x=[item['_id']],
            y=[item[selected_category]],
            name=selected_category,
            orientation='v',
            showlegend=False
        ))

    # Update layout with autoscaling and more space for y-axis labels
    fig.update_layout(
        title=f'{selected_category} by hours',
        yaxis_title=selected_category,
        xaxis_title='Street',
        xaxis={'automargin': True},  # Enable automargin for x-axis
        margin=dict(l=80, r=50, t=50, b=50),  # Adjust margins for wider grid and space for additional info
        width=150 + 50 * len(data),
        yaxis=dict(side='top'),
        showlegend=False,
        height=400
    )

    return fig
