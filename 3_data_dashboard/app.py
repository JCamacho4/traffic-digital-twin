import json

import dash
import pandas as pd
from dash import Dash
from dash.dependencies import Input, Output, State
from dash.html import Ul, Li, Thead, Tr, Tbody, Td, Th, Label, Br, Button, Div, Img, H1
from dash_sylvereye import SylvereyeRoadNetwork
import dash_bootstrap_components as dbc
from dash import dcc

from dashboardfunctions import constants
from dashboardfunctions.color import color_by_attribute
from dashboardfunctions.mongo import get_database, get_available_graphs_by_date, get_graph_by_filename, \
    get_edges_by_filename, get_data_from_graphs_with_filters_by_name, get_data_from_graphs_with_filters_by_hours, \
    get_data_from_graphs_with_filters_by_weekday
from dashboardfunctions.utils import get_node_edge_options, get_road_data_from_graph_with_dictionary, \
    add_info_from_mongo_list, get_min_max_values_from_attribute_edges_data, \
    get_marks_each_60_minutes_with_half_hour_marks, translate_float_array_to_hour_string

from dashboardfunctions.graphics import create_arrows, create_horizontal_bars_by_name_graph, \
    create_vertical_bars_by_hours_graph, create_horizontal_bars_by_weekday_graph

from datetime import date, datetime

# =====================================================================================================================
#                                    LOAD THE DATA FROM THE  BASE GRAPH
# =====================================================================================================================


node_options, edge_options = get_node_edge_options()
nodes_data, edges_data, graph = get_road_data_from_graph_with_dictionary('graph_output/base_graph.graphml')
mongo_database = get_database("TFG")
current_datetime_graph = None

# SOME INFORMATION THAT WILL BE RETRIEVED FROM THE DATABASE AND WILL BE USED TO FILTER THE DATA
# AND TO DISPLAY THE INFORMATION ON THE DASHBOARD

last_data_by_street_name = []
last_data_by_hours = []
last_data_by_weekday = []
# =====================================================================================================================
#                                    BUILD THE LAYOUT OF THE DASHBOARD
# =====================================================================================================================


app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app._favicon = "favicon"
app.title = "Traffic Levels Data Dashboard"
app.layout =  dbc.Container([

        dbc.Row([
            dbc.Col([
                # Use a div with flex properties to align the image and text horizontally
                Div([
                    Img(src=app.get_asset_url("favicon_image.png"),
                                  style={'width': '50px', 'margin-right': '15px'}),
                    H1("Traffic Levels Data Dashboard", className="text-center",
                                 style={'fontWeight': 'bold', 'fontSize': '40px', 'display': 'inline-block'}),
                    Img(src=app.get_asset_url("favicon_image.png"),
                                  style={'width': '50px', 'margin-left': '15px'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'paddingBottom':'15px'})
            ], width=12)
        ]),

        dbc.Card([
            dbc.CardHeader("Filters for extracting data", style={'fontWeight': 'bold', 'fontSize': '18px'}),
            dbc.CardBody([

                dbc.Row([

                    dbc.Col([
                        dbc.Label("Data date range", style={'fontWeight': 'bold'}),
                        Br(),
                        dbc.Label("Data in this data range will be displayed in the graphs",
                                  style={'fontSize': '14px'}),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=date(2024, 5, 8),
                            max_date_allowed=date(2024, 8, 31),
                            start_date_placeholder_text="Information from",
                            end_date_placeholder_text="Information until",
                            start_date=date(2024, 5, 8),
                            end_date=date(2024, 8, 31),
                            first_day_of_week=1,
                        ),
                    ], width=3),

                    dbc.Col([
                        dbc.Label("Names ", style={'fontWeight': 'bold'}),
                        Br(),
                        dbc.Label("Streets can be filtered by more than one name separating them with a comma ',' ",
                                  style={'fontSize': '14px'}),
                        Br(),
                        dcc.Input(
                            id='name-input',
                            type='text',
                            placeholder='Enter a name',
                            style={'width': '90%'}
                        ),
                    ], width=5),

                    dbc.Col([
                        dbc.Label("Street type", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='street-type-checklist',
                            options=[
                                {'label': 'Primary', 'value': 'primary'},
                                {'label': 'Secondary', 'value': 'secondary'},
                                {'label': 'Tertiary', 'value': 'tertiary'},
                                {'label': 'Motorway', 'value': 'motorway'},
                                {'label': 'Motorway Link', 'value': 'motorway_link'},
                                {'label': 'Residential', 'value': 'residential'},
                                {'label': 'Living Street', 'value': 'living_street'},
                                {'label': 'Primary Link', 'value': 'primary_link'},
                                {'label': 'Secondary Link', 'value': 'secondary_link'},
                                {'label': 'Tertiary Link', 'value': 'tertiary_link'},
                            ],
                            multi=True,
                            value=['secondary', 'motorway', 'motorway_link', 'primary', 'tertiary', 'residential',
                                   'primary_link', 'tertiary_link', 'secondary_link', 'living_street']
                        ),
                    ], width=4),
                ]),

                dbc.Row([
                    dbc.Col([

                        dbc.Label("Hours range", style={'fontWeight': 'bold'}),
                        dcc.RangeSlider(
                            id='hours-range-slider',
                            min=0,
                            max=24,
                            marks=get_marks_each_60_minutes_with_half_hour_marks(),
                            # marks={0:'00:00', 2:'00:30'},
                            tooltip={"placement": "bottom", "always_visible": False},
                            step=0.25,
                            value=[0, 24]
                        ),
                    ], width=12),
                ], style={'marginTop': '10px'}),

                dbc.Row([
                    dbc.Col([
                        dbc.Modal(
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Data processing completed")),
                                dbc.ModalBody("The data has been processed successfully. You can now download the data "
                                              "and study the graphs at the bottom of the page."),
                            ],
                            id='finish-dialog',
                            is_open=False,
                        ),
                        dcc.Loading(
                            id="loading-spinner",
                            children=[
                                dbc.Button("Process",
                                           id="button-submit-filter",
                                           n_clicks=0,
                                           style={'padding': '15px', 'fontSize': '18px', 'fontWeight': 'bold'}, )
                            ],
                            type="circle"
                        ),
                    ], width=12, className="d-flex justify-content-center"),

                    dbc.Col([
                        dbc.Button("Download data by streets", id="button-download-street", n_clicks=0,
                                   disabled=True,
                                   color="success", style={'marginRight': '10px'}),
                        dcc.Download(id="download-street"),
                        dbc.Button("Download data by hours", id="button-download-hour", n_clicks=0, disabled=True,
                                   color="success", style={'marginLeft': '10px', 'marginRight': '10px'}),
                        dcc.Download(id="download-hour"),
                        dbc.Button("Download data by days", id="button-download-day-of-week", n_clicks=0,
                                   disabled=True,
                                   color="success", style={'marginLeft': '10px'}),
                        dcc.Download(id="download-day-of-week"),
                    ], width=12, className="d-flex justify-content-center", style={'marginTop': '15px'}),


                ], className="align-items-center", style={'marginTop': '20px'})
            ]),

        ]),

        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Node Information", style={'fontWeight': 'bold', 'fontSize': '18px'}),
                    dbc.CardBody([
                        dbc.Table([
                            Thead(Tr([
                                Th("Property", style={'width': '40%'}),
                                Th("Value", style={'width': '60%'})
                            ])),
                            Tbody([
                                Tr([Td("Latitude"), Td(id='node-x')]),
                                Tr([Td("Longitude"), Td(id='node-y')]),
                                Tr([Td("Street Count"), Td(id='node-street-count')]),
                                Tr([Td("Crossing"), Td(id='node-crossing')]),
                                Tr([Td("Traffic Light"), Td(id='node-traffic-light')]),
                                Tr([Td("OSM ID"), Td(id='node-osmid')]),
                            ])
                        ], style={'table-layout': 'fixed', 'width': '100%'})
                    ])
                ]),

                dbc.Card([
                    dbc.CardHeader("Edge Information", style={'fontWeight': 'bold', 'fontSize': '18px'}),
                    dbc.CardBody([

                        dbc.Table([
                            Thead(Tr([
                                Th("Property", style={'width': '40%'}),
                                Th("Value", style={'width': '60%'})
                            ])),
                            Tbody([
                                Tr([Td("Name"), Td(id='edge-name')]),
                                Tr([Td("Maxspeed"), Td(id='edge-maxspeed')]),
                                Tr([Td("Highway"), Td(id='edge-highway')]),
                                Tr([Td("Traffic level"), Td(id='edge-traffic-level')]),
                                Tr([Td("Current Speed"), Td(id='edge-current-speed')]),
                                Tr([Td("Lanes"), Td(id='edge-lanes')]),
                                Tr([Td("OSM ID"), Td(id='edge-osmid')])
                            ])
                        ], style={'table-layout': 'fixed', 'width': '100%'}),

                        # Render the arrows that represent the direction of the edge(s)
                        dcc.Graph(id='direction-arrows',
                                  style={'width': '100%', 'height': '23vh', 'margin': 'auto'})

                    ])
                ], style={'marginTop': '20px'}),
            ], width=2),

            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Road Network", style={'fontWeight': 'bold', 'fontSize': '18px'}),
                    dbc.CardBody(
                        SylvereyeRoadNetwork(
                            id='sylvereye-roadnet',
                            tile_layer_url=constants.SET_UP.get("TILE_LAYER_URL"),
                            tile_layer_subdomains=constants.SET_UP.get("TILE_LAYER_SUBDOMAINS"),
                            tile_layer_attribution=constants.SET_UP.get("TILE_LAYER_ATTRIBUTION"),
                            map_center=constants.SET_UP.get("MAP_CENTER"),
                            map_zoom=constants.SET_UP.get("MAP_ZOOM"),
                            map_style=constants.SET_UP.get("MAP_STYLE"),
                            nodes_data=nodes_data,
                            edges_data=edges_data,
                            tile_layer_opacity=constants.SET_UP.get("TILE_LAYER_OPACITY"),
                            node_options=node_options,
                            edge_options=edge_options
                        )
                    )
                ]),
            ], width=8),

            dbc.Col([

                dbc.Card([
                    dbc.CardHeader("Date picker", style={'fontWeight': 'bold', 'fontSize': '18px'}),
                    dbc.CardBody([
                        dbc.Label("Display on map", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='date-hour-dropdown',
                            placeholder="Select a date to be displayed on the map:",
                            options=[],
                        )

                    ])
                ], style={}),

                dbc.Card([
                    dbc.CardHeader("Nodes display options", style={'fontWeight': 'bold', 'fontSize': '18px'}),
                    dbc.CardBody([
                        dbc.Label("Size", style={'fontWeight': 'bold'}),
                        dcc.Slider(
                            id='node-size',
                            min=0,
                            max=0.002,
                            step=0.0001,
                            value=0.0008,
                            marks={0: 'Hide', 0.0008: 'Default', 0.002: 'Biggest'}
                        ),
                        dbc.Label("Transparency", style={'fontWeight': 'bold'}),
                        dcc.Slider(
                            id='node-transparency',
                            min=0,
                            max=1,
                            step=0.25,
                            value=2,
                            marks={0: 'Hide', 1: 'Full'}
                        ),

                        dbc.Label("Show", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            multi=True,
                            id='node-type-show',
                            options=[
                                {'label': 'Traffic Lights', 'value': 'traffic_light'},
                                {'label': 'Crossings', 'value': 'crossing'},
                                {'label': 'Empty', 'value': 'None'},
                            ],
                            value=['traffic_light', 'crossing', 'None']
                        ),

                    ])
                ], style={'marginTop': '20px'}),

                dbc.Card([

                    dbc.CardHeader("Edges display options", style={'fontWeight': 'bold', 'fontSize': '18px'}),
                    dbc.CardBody([
                        dbc.Label("Width", style={'fontWeight': 'bold'}),
                        dcc.Slider(
                            id='edge-width',
                            min=0,
                            max=0.125,
                            step=0.005,
                            value=0.05,
                            marks={0: 'Hide', 0.05: 'Default', 0.125: 'Biggest'}
                        ),
                        dbc.Label("Transparency", style={'fontWeight': 'bold'}),
                        dcc.Slider(
                            id='edge-transparency',
                            min=0,
                            max=1,
                            step=0.25,
                            value=1,
                            marks={0: 'Hide', 1: 'Full'}
                        ),
                        dbc.Label("Color", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='edge-color-by',
                            options=[
                                {'label': 'Traffic Level', 'value': 'traffic_level'},
                                {'label': 'Maxspeed', 'value': 'maxspeed'},
                                {'label': 'Current Speed', 'value': 'current_speed'},
                            ],
                            value='traffic_level',
                            clearable=False
                        ),

                        Br(),

                        dbc.Label("Traffic level range", style={'fontWeight': 'bold'}),
                        dcc.RangeSlider(
                            id='range-slider-traffic-level',
                            min=0,
                            max=1,
                            step=0.001,
                            value=[0, 1],
                            marks={0: '0', 0.25: '0.25', 0.5: '0.5', 0.75: '0.75', 1: '1'},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),

                        Br(),

                        dbc.Label("Display", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            multi=True,
                            id='edge-api-data',
                            options=[
                                {'label': 'API', 'value': 'True'},
                                {'label': 'Normalization', 'value': 'False'},
                            ],
                            value=['True', 'False']
                        ),

                    ])
                ], style={'marginTop': '20px'}),

            ], width=2),

        ], style={'marginTop': '20px'}),

        dbc.Card([
            dbc.CardHeader("Graphs", style={'fontWeight': 'bold', 'fontSize': '18px'}),
            dbc.CardBody([
                dbc.Row([
                    dcc.Dropdown(
                        id='category-graphs-dropdown',
                        options=[
                            {'label': 'Avg Traffic Level', 'value': 'avgTrafficLevel'},
                            {'label': 'Min Traffic Level', 'value': 'minTrafficLevel'},
                            {'label': 'Max Traffic Level', 'value': 'maxTrafficLevel'},
                            {'label': 'Median Traffic Level', 'value': 'medianTrafficLevel'},
                            {'label': 'Avg Current Speed', 'value': 'avgCurrentSpeed'},
                            {'label': 'Min Current Speed', 'value': 'minCurrentSpeed'},
                            {'label': 'Max Current Speed', 'value': 'maxCurrentSpeed'},
                            {'label': 'Median Current Speed', 'value': 'medianCurrentSpeed'}
                        ],
                        value='avgTrafficLevel',
                        style={'width': '100%'}
                    ),
                ]),
                dbc.Row([
                    Div([
                        dcc.Graph(id='verticals-bars-graph-by-hours'),
                    ], style={'marginTop': '10px'})  # 'overflowX': 'scroll'})
                ]),

                dbc.Row([
                    dbc.Col([
                        Div([
                            dcc.Graph(id='horizontal-bars-graph-by-streets'),
                        ], style={'overflowY': 'scroll', 'height': '450px', 'marginTop': '20px'})
                    ], width=6),
                    dbc.Col([
                        Div([
                            dcc.Graph(id='vertical-bars-graph-by-weekday'),
                        ], style={'height': '450px', 'marginTop': '20px'})  # 'overflowY': 'scroll'
                    ], width=6),
                ]),

            ]),
        ], style={'marginTop': '20px'}),

    ], fluid=True, style={'backgroundColor': '#f0f0f0','paddingTop': '20px', 'paddingBottom': '20px', 'paddingLeft': '8%', 'paddingRight': '8%'})


# =====================================================================================================================
#                                CONTROL THE INTERACTIONS BETWEEN THE COMPONENTS
# =====================================================================================================================

@app.callback(
    Output("date-hour-dropdown", "options"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
    Input("hours-range-slider", "value"),
)
def update_available_dates_dropdown(start_date, end_date, hours_range_slider):
    print("Updating available dates dropdown")
    if start_date is not None and end_date is not None:
        start_date_object = date.fromisoformat(start_date)
        end_date_object = date.fromisoformat(end_date)

        # Convert date to datetime for MongoDB compatibility
        start_datetime = datetime.combine(start_date_object, datetime.min.time())
        end_datetime = datetime.combine(end_date_object, datetime.min.time())

        # Add 23 hours and 59 minutes to the end date
        end_datetime = end_datetime.replace(hour=23, minute=59)

        available_dates = get_available_graphs_by_date(mongo_database, start_datetime, end_datetime)

        start_hour_minutes_string, end_hour_minutes_string = translate_float_array_to_hour_string(hours_range_slider)
        available_dates = [date for date in available_dates if
                           start_hour_minutes_string <= date.get("datetime").strftime(
                               "%H:%M") <= end_hour_minutes_string]

        dates_list = []
        for i in available_dates:
            object_date = i.get("datetime")
            object_string = object_date.strftime("%Y/%m/%d - ") + i.get("day_of_week") + object_date.strftime(
                " - %H:%M  ")
            dates_list.append({'label': object_string, 'value': i.get("filename_extensions")})

        return dates_list


@app.callback(
    [Output('node-x', 'children'),
     Output('node-y', 'children'),
     Output('node-street-count', 'children'),
     Output('node-crossing', 'children'),
     Output('node-traffic-light', 'children'),
     Output('node-osmid', 'children')],
    [Input('sylvereye-roadnet', 'clicked_node')]
)
def update_node_data(clicked_node):
    print("Updating node data")
    if clicked_node:
        node_data = clicked_node["data"]["data"]
        crossing = 'Yes' if node_data.get("highway") == "crossing" else 'No'
        traffic_light = 'Yes' if node_data.get("traffic_light") else 'No'
        return [
            node_data.get("x", "N/A") if node_data.get("x") != "" else "N/A",
            node_data.get("y", "N/A") if node_data.get("y") != "" else "N/A",
            node_data.get("street_count", "N/A") if node_data.get("street_count") != "" else "N/A",
            crossing,
            traffic_light,
            node_data.get("osmid", "N/A") if node_data.get("osmid") != "" else "N/A"
        ]
    return ["N/A"] * 6


@app.callback(
    [Output('edge-name', 'children'),
     Output('edge-maxspeed', 'children'),
     Output('edge-highway', 'children'),
     Output('edge-traffic-level', 'children'),
     Output('edge-current-speed', 'children'),
     Output('edge-lanes', 'children'),
     Output('edge-osmid', 'children'),
     Output('direction-arrows', 'figure')
     ],
    Input('sylvereye-roadnet', 'clicked_edge'),
    Input('edge-color-by', 'value'),

)
def update_edge_data(clicked_edge, edge_color_by):
    print("Updating edge data")
    if clicked_edge and edge_color_by is not None:
        global edges_data

        edge_data = clicked_edge["data"]["data"]
        edge_bearing = edge_data.get("bearing")
        # It's necessary to convert the value to float, because 'click_edge' makes some conversions
        if edge_data.get(edge_color_by) is None or edge_data.get(edge_color_by) == "None":
            edge_color_value = None
        else:
            edge_color_value = float(edge_data.get(edge_color_by))

        source_node = edge_data.get("source_osmid")
        target_node = edge_data.get("target_osmid")

        if not edge_data.get("oneway"):
            opposite_edge_data = [edge for edge in edges_data if
                                  edge["data"]["source_osmid"] == target_node and edge["data"][
                                      "target_osmid"] == source_node][0]

            if opposite_edge_data["data"][edge_color_by] is None or opposite_edge_data["data"][edge_color_by] == "None":
                opposite_edge_color_value = None
            else:
                opposite_edge_color_value = float(opposite_edge_data["data"][edge_color_by])

        else:
            opposite_edge_color_value = -1

        if edge_color_by != "traffic_level":
            min_val, max_val = get_min_max_values_from_attribute_edges_data(edges_data, attribute=edge_color_by)
            print(min_val, max_val)
        else:
            min_val, max_val = 0, 1

        return [
            edge_data.get("name", "N/A") if edge_data.get("name") != "" else "N/A",
            edge_data.get("maxspeed", "N/A") if edge_data.get("maxspeed") != "" else "N/A",
            edge_data.get("highway", "N/A") if edge_data.get("highway") != "" else "N/A",
            round(float(edge_data.get("traffic_level", "N/A")), 3) if edge_data.get(
                "traffic_level") != "" and edge_data.get(
                "traffic_level") is not None else "N/A",
            round(float(edge_data.get("current_speed", "N/A")), 3) if edge_data.get(
                "current_speed") != "" and edge_data.get(
                "current_speed") is not None else "N/A",
            edge_data.get("lanes", "N/A") if edge_data.get("lanes") != "" else "N/A",
            edge_data.get("osmid", "N/A") if edge_data.get("osmid") != "" else "N/A",
            create_arrows(edge_bearing, tl_1=edge_color_value, tl_2=opposite_edge_color_value, min_val=min_val,
                          max_val=max_val) if not edge_data.get(
                "oneway") else create_arrows(edge_bearing, tl_1=edge_color_value, min_val=min_val, max_val=max_val)
        ]
    return ["N/A"] * 7 + [create_arrows(0, tl_1=-1, tl_2=-1)]


@app.callback(
    Output('sylvereye-roadnet', 'edges_data'),
    Output('sylvereye-roadnet', 'nodes_data'),
    Input('range-slider-traffic-level', 'value'),
    Input('node-type-show', 'value'),
    Input('date-hour-dropdown', 'value'),
    Input('edge-color-by', 'value'),
    Input('edge-api-data', 'value'),

    Input('name-input', 'value'),
    Input('street-type-checklist', 'value'),
)
def update_graph_displayed_map(range_slider_traffic_level, node_type_show, date_hour_dropdown, edge_color_by,
                               edge_api_data, name_input, street_type_checklist):
    print("Loading different graph")
    global nodes_data, edges_data, current_datetime_graph

    # Reload the base graph to a new graph with the selected date and hour
    if date_hour_dropdown is not None and current_datetime_graph != date_hour_dropdown:
        edges_list_from_date_hour = get_edges_by_filename(mongo_database, date_hour_dropdown)

        if edges_list_from_date_hour is not None and len(edges_list_from_date_hour) > 0:
            edges_data = add_info_from_mongo_list(edges_list_from_date_hour, edges_data)
            current_datetime_graph = date_hour_dropdown
        else:
            print("No data found for the selected date and hour.")

    # Color by attribute
    if edge_color_by is not None:
        min_val, max_val = get_min_max_values_from_attribute_edges_data(edges_data, attribute=edge_color_by)
        color_by_attribute(edges_data, attribute=edge_color_by, min_val=min_val, max_val=max_val)

    # Filter by traffic level
    edges_data_filtered = [edge for edge in edges_data if edge["data"]["traffic_level"] is None or
                           range_slider_traffic_level[0] <= edge["data"]["traffic_level"] <= range_slider_traffic_level[
                               1]]

    # Filter by API data
    if edge_api_data is not None and len(edge_api_data) > 0:
        edges_data_filtered = [edge for edge in edges_data_filtered
                               if 'api_data' in edge["data"] and
                               (edge["data"]["api_data"] is None
                                or
                                str(edge["data"]["api_data"]) in edge_api_data)]

    # Filter by name
    if name_input is not None and len(name_input) > 0:
        list_names = name_input.split(",")
        list_names = [name.lower().strip() for name in list_names if
                      name.strip()]  # Strip whitespace, convert to lower case, and exclude empty strings
        edges_data_filtered = [
            edge for edge in edges_data_filtered
            if 'name' in edge["data"] and edge["data"]["name"] is not None
               and any(partial_name in edge["data"]["name"].lower() for partial_name in list_names)
        ]
    # Filter by street type
    if street_type_checklist is not None and len(street_type_checklist) > 0:
        edges_data_filtered = [edge for edge in edges_data_filtered if edge["data"]["highway"] in street_type_checklist]

    # Don't show nodes that are not connected to any edge
    nodes_connected_to_edges = []
    for edge in edges_data_filtered:
        if edge["data"]["source_osmid"] not in nodes_connected_to_edges:
            nodes_connected_to_edges.append(edge["data"]["source_osmid"])
        if edge["data"]["target_osmid"] not in nodes_connected_to_edges:
            nodes_connected_to_edges.append(edge["data"]["target_osmid"])

    # Filter by node type
    show_nodes_osmids = []
    for node in nodes_data:
        print(node)
        # Get node type (highway) and traffic light status
        node_type = str(node["data"].get("highway", ""))  # Default to empty string if not present
        node_tl = node["data"].get("traffic_light", False)  # Default to False if not present

        # Check if node type or traffic light should be shown, based on node_type_show
        should_show = False

        if node_type and node_type in node_type_show:
            should_show = True  # Node type (highway) matches
        elif node_tl and "traffic_light" in node_type_show:
            should_show = True  # Traffic light node is selected

        # Only include nodes that should be shown and are connected to edges
        if should_show and node["data"]["osmid"] in nodes_connected_to_edges:
            show_nodes_osmids.append(node["data"]["osmid"])

    nodes_data_filtered = [node for node in nodes_data if node["data"]["osmid"] in show_nodes_osmids]

    return edges_data_filtered, nodes_data_filtered


@app.callback(
    Output('sylvereye-roadnet', 'node_options'),
    Output('sylvereye-roadnet', 'edge_options'),

    Input('node-size', 'value'),
    Input('node-transparency', 'value'),
    Input('edge-width', 'value'),
    Input('edge-transparency', 'value'),
)
def update_display(node_size, node_transparency, edge_width, edge_transparency):
    print("Updating display")
    node_options["size_default"] = node_size
    node_options["alpha_default"] = node_transparency

    edge_options["width_default"] = edge_width
    edge_options["alpha_default"] = edge_transparency

    return node_options, edge_options


@app.callback(
    Output("horizontal-bars-graph-by-streets", "figure", allow_duplicate=True),
    Output("verticals-bars-graph-by-hours", "figure", allow_duplicate=True),
    Output("vertical-bars-graph-by-weekday", "figure", allow_duplicate=True),

    Output("button-download-street", "disabled"),
    Output("button-download-hour", "disabled"),
    Output("button-download-day-of-week", "disabled"),

    Output("loading-spinner", "children"),
    Output("finish-dialog", "is_open"),

    Input("button-submit-filter", "n_clicks"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
    State('street-type-checklist', 'value'),
    State("hours-range-slider", "value"),
    State('name-input', 'value'),
    State('category-graphs-dropdown', 'value'),
    prevent_initial_call=True
)
def update_data_selection_output(n_clicks, start_date, end_date, street_type_checklist, hours_range_slider, name_input,
                                 selected_category):
    print("Updating data selection")
    global last_data_by_street_name, last_data_by_hours, last_data_by_weekday

    if n_clicks == 0:
        return (create_horizontal_bars_by_name_graph([], selected_category),
                create_vertical_bars_by_hours_graph([], selected_category))

    if start_date is not None and end_date is not None:
        start_date_object = date.fromisoformat(start_date)
        end_date_object = date.fromisoformat(end_date)

        # Convert date to datetime for MongoDB compatibility
        start_datetime = datetime.combine(start_date_object, datetime.min.time())
        end_datetime = datetime.combine(end_date_object, datetime.min.time())

        # Add 23 hours and 59 minutes to the end date
        end_datetime = end_datetime.replace(hour=23, minute=59)

    # Get 'hours:minutes' from the slider
    start_hour, end_hour = translate_float_array_to_hour_string(hours_range_slider)

    # Get the names
    list_names = []
    if name_input is not None and len(name_input) > 0:
        list_names = name_input.split(",")
        list_names = [name.lower().strip() for name in list_names if
                      name.strip()]  # Strip whitespace, convert to lower case, and exclude empty strings

    import time

    # Timer for fetching data by name
    start_time = time.time()
    mongo_data_cursor = get_data_from_graphs_with_filters_by_name(mongo_database, start_datetime, end_datetime,
                                                                  list_names, street_type_checklist, start_hour,
                                                                  end_hour)
    last_data_by_street_name = list(mongo_data_cursor)
    end_time = time.time()
    time_taken_by_name = end_time - start_time
    print(last_data_by_street_name)
    print(f"Time taken to fetch data by name: {time_taken_by_name:.2f} seconds")

    # Timer for fetching data by hours
    start_time = time.time()
    mongo_data_cursor = get_data_from_graphs_with_filters_by_hours(mongo_database, start_datetime, end_datetime,
                                                                   list_names, street_type_checklist, start_hour,
                                                                   end_hour)
    last_data_by_hours = list(mongo_data_cursor)
    end_time = time.time()
    time_taken_by_hours = end_time - start_time
    print(last_data_by_hours)
    print(f"Time taken to fetch data by hours: {time_taken_by_hours:.2f} seconds")

    # Timer for fetching data by day of the week
    start_time = time.time()
    mongo_data_cursor = get_data_from_graphs_with_filters_by_weekday(mongo_database, start_datetime, end_datetime,
                                                                     list_names, street_type_checklist, start_hour,
                                                                     end_hour)
    last_data_by_weekday = list(mongo_data_cursor)
    end_time = time.time()
    time_taken_by_weekday = end_time - start_time
    print(last_data_by_weekday)
    print(f"Time taken to fetch data by weekday: {time_taken_by_weekday:.2f} seconds")

    return (create_horizontal_bars_by_name_graph(last_data_by_street_name, selected_category),
            create_vertical_bars_by_hours_graph(last_data_by_hours, selected_category),
            create_horizontal_bars_by_weekday_graph(last_data_by_weekday, selected_category),
            False, False, False,  # Download buttons are enabled
            dash.no_update,  # Allow process data again
            True,  # Show dialog
            )


@app.callback(
    Output('horizontal-bars-graph-by-streets', 'figure'),
    Output('verticals-bars-graph-by-hours', 'figure'),
    Output('vertical-bars-graph-by-weekday', 'figure'),

    Input('category-graphs-dropdown', 'value')
)
def update_graphs(selected_category):
    print("Updating graphs category: " + selected_category)
    return (create_horizontal_bars_by_name_graph(last_data_by_street_name, selected_category),
            create_vertical_bars_by_hours_graph(last_data_by_hours, selected_category),
            create_horizontal_bars_by_weekday_graph(last_data_by_weekday, selected_category)
            )


@app.callback(
    Output("download-street", "data"),
    Input("button-download-street", "n_clicks"))
def download_data_by_street(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update

    global last_data_by_street_name

    df = pd.DataFrame(last_data_by_street_name)
    csv = df.to_csv()

    return dict(content=csv, filename="data_street.csv")


@app.callback(
    Output("download-hour", "data"),
    Input("button-download-hour", "n_clicks"))
def download_data_by_hour(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update

    global last_data_by_hours

    df = pd.DataFrame(last_data_by_hours)
    csv = df.to_csv()

    return dict(content=csv, filename="data_hour.csv")


@app.callback(
    Output("download-day-of-week", "data"),
    Input("button-download-day-of-week", "n_clicks"))
def download_data_by_day_of_week(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return dash.no_update

    global last_data_by_weekday

    df = pd.DataFrame(last_data_by_weekday)
    csv = df.to_csv()

    return dict(content=csv, filename="data_day_of_week.csv")


if __name__ == '__main__':
    app.run_server(port=8051)
