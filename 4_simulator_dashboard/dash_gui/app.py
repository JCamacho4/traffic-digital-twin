import copy
import json
import time

import pandas as pd

from dash import Dash, no_update
from dash.dash_table import DataTable
from dash.dependencies import Input, Output, State
from dash.html import Ul, Li, Thead, Tr, Tbody, Td, Th, Label, Br, Button, Progress, Pre
from dash.long_callback import DiskcacheLongCallbackManager
from dash_sylvereye import SylvereyeRoadNetwork
import dash_bootstrap_components as dbc

from dash import html
from dash import dcc

from dashboardfunctions import constants
from dashboardfunctions.color import color_by_attribute
from dashboardfunctions.mongo import get_database, get_available_graphs_by_date, get_edges_by_filename
from dashboardfunctions.utils import get_node_edge_options, get_road_data_from_graph_with_dictionary, \
    add_info_from_mongo_list, get_min_max_values_from_attribute_edges_data, \
    translate_float_array_to_hour_string, add_info_from_mesa_list, analyze_and_plot_simulation_data, get_simulation_name

from dashboardfunctions.graphics import create_arrows

from datetime import date, datetime

from traffic_model.run import run_simulation

import plotly.graph_objects as go

## Diskcache
import diskcache

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

# =====================================================================================================================
#                                    LOAD THE DATA FROM THE  BASE GRAPH
# =====================================================================================================================

mongo_database = get_database("TFG")
node_options, edge_options = get_node_edge_options()
nodes_data, edges_data, graph = get_road_data_from_graph_with_dictionary('./base_graph.graphml')

traffic_level_file = copy.deepcopy(edges_data)
traffic_level_simulation = copy.deepcopy(edges_data)

current_datetime_graph = None

# SOME INFORMATION THAT WILL BE RETRIEVED FROM THE DATABASE AND WILL BE USED TO FILTER THE DATA
# AND TO DISPLAY THE INFORMATION ON THE DASHBOARD

last_data_by_street_name = []
last_data_by_hours = []

# =====================================================================================================================
#                                    BUILD THE LAYOUT OF THE DASHBOARD
# =====================================================================================================================


app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], long_callback_manager=long_callback_manager)
app.title = "Traffic simulator"
app._favicon = "favicon.ico"
app.layout = dbc.Container([
    dcc.Store(id='traffic-level-simulation-store'),
    dcc.Store(id='data-simulation-store'),

    dbc.Row([
        dbc.Col([
            # Use a div with flex properties to align the image and text horizontally
            html.Div([
                html.Img(src=app.get_asset_url("favicon.ico"),
                         style={'height': '50px', 'margin-right': '15px'}),
                html.H1("Traffic Simulator", className="text-center",
                        style={'fontWeight': 'bold', 'fontSize': '40px', 'display': 'inline-block'}),
                html.Img(src=app.get_asset_url("favicon.ico"),
                         style={'height': '50px', 'margin-left': '15px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'paddingBottom':'15px' })
        ], width=12)
    ]),

    dbc.Card([
        dbc.CardHeader("Simulation's parameters", style={'fontWeight': 'bold', 'fontSize': '18px'}),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        dbc.Label("Number of steps", style={'fontWeight': 'bold'}),
                        dcc.Input(
                            id='input-steps',
                            type='number',
                            value=100,
                            min=1,
                            max=1_000_000,
                            style={'width': '100%'}
                        ),
                        Br(),
                        dbc.Label("Number of agents", style={'fontWeight': 'bold'}),
                        dcc.Input(
                            id='input-agents',
                            type='number',
                            value=100,
                            min=1,
                            max=5_000,
                            style={'width': '100%'}
                        ),
                        Br(),
                        dbc.Label("Enable respawn of the agents", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='agent-respawn-dropdown',
                            placeholder="Respawn enabled",
                            options=[
                                {'label': 'Yes', 'value': True},
                                {'label': 'No', 'value': False},
                            ],
                            style={'width': '100%'}
                        )
                    ], style={'height': '100%', 'display': 'flex', 'flexDirection': 'column',
                              'justifyContent': 'center', 'paddingLeft': '5%'}),
                ], width=2),

                dbc.Col([
                    html.Div([
                        dbc.Label("Routing method of the agents", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='agent-routing-dropdown',
                            placeholder="Routing method",
                            options=[
                                {'label': 'Random', 'value': 'random'},
                                {'label': 'Shortest path (start)', 'value': 'no_weight'},
                                {'label': 'Shortest path with weight (start) ', 'value': 'weight_start'},
                                {'label': 'Shortest path with weight (step) ', 'value': 'weight_step'}
                            ],
                            style={'width': '100%'}
                        ),
                        Br(),
                        dbc.Label("Start method of the agents", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='agent-start-dropdown',
                            placeholder="Start method",
                            options=[
                                {'label': 'Random', 'value': 'random'},
                                {'label': 'POIs', 'value': 'pois'},
                                {'label': 'Entry/Exit', 'value': 'entry_exit'}
                            ],
                            style={'width': '100%'}
                        ),
                        Br(),
                        dbc.Label("End method of the agents", style={'fontWeight': 'bold'}),
                        dcc.Dropdown(
                            id='agent-end-dropdown',
                            placeholder="End method",
                            options=[
                                {'label': 'Random', 'value': 'random'},
                                {'label': 'POIs', 'value': 'pois'},
                                {'label': 'Entry/Exit', 'value': 'entry_exit'}
                            ],
                            style={'width': '100%'}
                        )
                    ], style={'height': '100%', 'display': 'flex', 'flexDirection': 'column',
                              'justifyContent': 'center'}),
                ], width=2),

                dbc.Col([
                    html.Div([
                        dbc.Label("Traffic initialization", style={'fontWeight': 'bold'}),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=date(2024, 5, 8),
                            max_date_allowed=date(2024, 8, 31),
                            start_date_placeholder_text="Information from",
                            end_date_placeholder_text="Information until",
                            start_date=date(2024, 5, 8),
                            end_date=date(2024, 8, 31),
                            first_day_of_week=1,
                            style={'marginBottom': '15px', 'zIndex': 9000},
                        ),
                        dcc.Dropdown(
                            id='date-hour-dropdown',
                            placeholder="Simulation will start with this time's traffic levels",
                            options=[],
                        ),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Warning")),
                                dbc.ModalBody("You must fill in all the fields to start the simulation, including "
                                              "selecting a date for when the simulation will begin"),
                            ],
                            id='arguments-dialog',
                            is_open=False,
                        )
                    ], style={'height': '100%', 'display': 'flex', 'flexDirection': 'column',
                              'justifyContent': 'center', 'width': '90%', 'textAlign': 'center'}),
                ], width=3),

                dbc.Col([
                    html.Div([
                        dcc.Loading(
                            id="loading-spinner",
                            children=[
                                dbc.Button("Start simulation", id="button-submit-filter", n_clicks=0,
                                           style={'width': '100%', 'marginBottom': '25px'}, color="primary"),
                            ],
                            type="circle"
                        ),

                        Progress(id="progress_bar", value=str(0), style={'width': '100%', 'marginBottom': '25px'}),
                        dbc.Card([
                            dbc.CardHeader("Download last simulation (csv)",
                                           style={'fontWeight': 'bold', 'textAlign': 'center', 'fontSize': '18px'}),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Button("Agents data",
                                               id="btn-download-agents-data-simulation",
                                               disabled=True, style={'fontSize': '0.8em', 'marginRight': '10px'},
                                               color="success"),
                                    dcc.Download(id="download-agent-data-simulation"),

                                    dbc.Button("Graph", id="btn-download-map-simulation",
                                               disabled=True, style={'fontSize': '0.8em', 'marginRight': '10px'},
                                               color="success"),
                                    dcc.Download(id="download-map-simulation"),

                                    dbc.Button("Model's data",
                                               id="btn-download-model-data-simulation",
                                               disabled=True, style={'fontSize': '0.8em'},
                                               color="success"),
                                    dcc.Download(id="download-model-data-simulation"),

                                ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'})
                            ], style={'padding': '10px'})
                        ], style={}, id='card-download-options'),

                    ], style={'height': '100%', 'display': 'flex', 'flexDirection': 'column',
                              'justifyContent': 'center', 'alignItems': 'center'})

                ], width=3, style={'display': 'flex', 'alignItems': 'center'}),

                # Select to display simulation or date graph
                dbc.Col([
                    html.Div([
                        dbc.Label("Display graph from:",
                                  style={'width': '100%', 'textAlign': 'center', 'fontWeight': 'bold'}),
                        Br(),
                        dcc.Dropdown(
                            id='graph-display-dropdown',
                            options=[
                                {'label': 'Date', 'value': 'date'},
                                {'label': 'Simulation', 'value': 'simulation'},
                            ],
                            value='date',
                            clearable=False,
                            disabled=True,
                            style={'width': '100%'}
                        ),
                        dbc.Modal(
                            [
                                dbc.ModalHeader(dbc.ModalTitle("Simulation finished")),
                                dbc.ModalBody("Simulation finished successfully, if you want to load the new traffic "
                                              "levels of the roads, you can display it selecting it in the bottom "
                                              "right dropdown. \n You can download the data of the simulation with the "
                                              "buttons below. \n You can also run more simulations and compare the "
                                              "results with the graphs at the end of the page."),
                            ],
                            id="simulation-finished",
                            is_open=False,
                        ),
                    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center',
                              'justifyContent': 'center', 'height': '100%'})
                ], width=2, style={'display': 'flex', 'alignItems': 'center'}),

            ]),
        ]),

    ]),

    dbc.Row([

        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Node information", style={'fontWeight': 'bold', 'fontSize': '18px'}),
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
                dbc.CardHeader("Edge information", style={'fontWeight': 'bold', 'fontSize': '18px'}),
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
                        id='node-type-show',
                        multi=True,
                        options=[
                            {'label': 'Traffic Lights', 'value': 'traffic_light'},
                            {'label': 'Crossings', 'value': 'crossing'},
                            {'label': 'Empty', 'value': 'None'},
                        ],
                        value=['traffic_light', 'crossing', 'None']
                    ),

                ])
            ], ),

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
                ])
            ], style={'marginTop': '20px'}),

            dbc.Card([
                dbc.CardHeader("Streets filter", style={'fontWeight': 'bold', 'fontSize': '18px'}),
                dbc.CardBody([
                    dbc.Label("Name", style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='name-input',
                        type='text',
                        placeholder='Split multiple names with commas "," ',
                        style={'width': '100%'}
                    ),
                    Br(),
                    Br(),
                    dbc.Label("Type", style={'fontWeight': 'bold'}),
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
                ], style={'marginTop': '-10px'}),
            ], style={'marginTop': '20px'}),

        ], width=2),

    ], style={'marginTop': '20px'}),

    dbc.Card([
        dbc.CardHeader("Results of the simulation", style={'fontWeight': 'bold', 'fontSize': '18px'}),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='avg-travel-time'),
                ], width=6, style={'alignItems': 'center'}),

                dbc.Col([
                    dcc.Graph(id='avg-waiting-time', ),
                ], width=6, style={'alignItems': 'center'}),

            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(id='avg-additional-time', ),
                ], width=6, style={'alignItems': 'center'}),

                dbc.Col([
                    dcc.Graph(id='hist-waiting-time'),
                ], width=6, style={'alignItems': 'center'}),

            ]),

            dbc.Row([
                dbc.Col([
                    html.Div(id='summary-stats-table')
                ], width=8)
            ], justify='center')  # This centers the Col within the Row
        ]),

    ], style={'marginTop': '20px'}),

], fluid=True, style={'paddingTop': '20px', 'paddingBottom': '20px', 'width': '100%',
                      'paddingLeft': '8%', 'paddingRight': '8%', 'backgroundColor': '#f0f0f0'})


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

            print(opposite_edge_color_value)
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
    Output('sylvereye-roadnet', 'edges_data', allow_duplicate=True),
    Output('sylvereye-roadnet', 'nodes_data', allow_duplicate=True),
    Input('range-slider-traffic-level', 'value'),
    Input('node-type-show', 'value'),
    Input('date-hour-dropdown', 'value'),
    Input('edge-color-by', 'value'),

    Input('name-input', 'value'),
    Input('street-type-checklist', 'value'),

    Input('graph-display-dropdown', 'value'),

    State('traffic-level-simulation-store', 'data'),

    prevent_initial_call=True
)
def update_graph_displayed_map(range_slider_traffic_level, node_type_show, date_hour_dropdown, edge_color_by,
                               name_input, street_type_checklist, graph_display_dropdown,
                               traffic_level_simulation_store):
    print("Loading different graph", graph_display_dropdown, date_hour_dropdown)

    global nodes_data, edges_data, current_datetime_graph, traffic_level_file

    # Reload the base graph to a new graph with the selected date and hour
    if date_hour_dropdown is not None and current_datetime_graph != date_hour_dropdown and graph_display_dropdown == "date":
        print("Getting data from the database")
        edges_list_from_date_hour = get_edges_by_filename(mongo_database, date_hour_dropdown)

        if edges_list_from_date_hour is not None and len(edges_list_from_date_hour) > 0:
            traffic_level_file = add_info_from_mongo_list(edges_list_from_date_hour, traffic_level_file)
            edges_data = traffic_level_file
            current_datetime_graph = date_hour_dropdown
        else:
            print("No data found for the selected date and hour.")
    elif graph_display_dropdown == "simulation":
        print("Getting data from the simulation")
        # Convert to python object the json string
        if traffic_level_simulation_store is not None:
            traffic_level_simulation_store = json.loads(traffic_level_simulation_store)
        edges_data = traffic_level_simulation_store
    elif graph_display_dropdown == "date" and current_datetime_graph is not None and current_datetime_graph == date_hour_dropdown:
        print("Getting data from the previous graph")
        edges_data = traffic_level_file

    for edge in edges_data:
        if edge["data"]["traffic_level"] is None or edge["data"]["traffic_level"] == "None":
            print(f"EDGE WITHOUT TRAFFIC LEVEL:{edge['data']['source_osmid']} - {edge['data']['target_osmid']}")

    # Color by attribute
    if edge_color_by is not None:
        min_val, max_val = get_min_max_values_from_attribute_edges_data(edges_data, attribute=edge_color_by)
        color_by_attribute(edges_data, attribute=edge_color_by, min_val=min_val, max_val=max_val)

    # Filter by traffic level
    edges_data_filtered = [edge for edge in edges_data if edge["data"]["traffic_level"] is None or
                           range_slider_traffic_level[0] <= edge["data"]["traffic_level"] <= range_slider_traffic_level[
                               1]]

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
    Output("date-hour-dropdown", "options"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
)
def update_available_dates_dropdown(start_date, end_date):
    print("Updating available dates dropdown")
    if start_date is not None and end_date is not None:
        hours_range_slider = [0, 24]
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


@app.long_callback(
    Output('traffic-level-simulation-store', 'data'),
    Output('data-simulation-store', 'data'),

    Output('arguments-dialog', 'is_open'),
    Output('simulation-finished', 'is_open'),
    Output('graph-display-dropdown', 'disabled'),

    Output('btn-download-map-simulation', 'disabled'),
    Output('btn-download-agents-data-simulation', 'disabled'),
    Output('btn-download-model-data-simulation', 'disabled'),

    Output('avg-travel-time', 'figure'),
    Output('avg-waiting-time', 'figure'),
    Output('avg-additional-time', 'figure'),
    Output('hist-waiting-time', 'figure'),

    Output('summary-stats-table', 'children'),

    Input('button-submit-filter', 'n_clicks'),
    State('date-hour-dropdown', 'value'),
    State("input-agents", 'value'),
    State("input-steps", 'value'),
    State('agent-start-dropdown', 'value'),
    State('agent-end-dropdown', 'value'),
    State('agent-respawn-dropdown', 'value'),
    State('agent-routing-dropdown', 'value'),
    State('traffic-level-simulation-store', 'data'),

    State('avg-travel-time', 'figure'),
    State('avg-waiting-time', 'figure'),
    State('avg-additional-time', 'figure'),
    State('hist-waiting-time', 'figure'),
    running=[
        (Output('button-submit-filter', 'disabled'), True, False),
    ],
    progress=[Output("progress_bar", "value"), Output("progress_bar", "max")],
    prevent_initial_call=True,
)
def begin_simulation(set_progress,
                     n_clicks,
                     date_hour_dropdown, num_agents, steps, agents_start_method,
                     agents_end_method, respawn_enabled, routing_method, traffic_level_simulation_stored,
                     fig_avg_travel_time, fig_avg_waiting_time, fig_avg_additional_time, fig_hist_waiting_time):
    global traffic_level_simulation
    print("Simulation function")

    # Initialize the progress bar
    set_progress((0, steps))

    if (date_hour_dropdown is not None
            and num_agents is not None
            and steps is not None
            and agents_start_method is not None
            and agents_end_method is not None
            and respawn_enabled is not None
            and routing_method is not None):

        inicio = time.time()

        # RUN THE SIMULATION
        (sim_traffic,
         sim_model_data,
         sim_agent_data) = run_simulation(steps,
                                          num_agents,
                                          date_hour_dropdown,
                                          start=agents_start_method,
                                          end=agents_end_method,
                                          respawn=respawn_enabled,
                                          routing=routing_method,
                                          # Logging configuration
                                          enable_movement=False,
                                          enable_respawning=False,
                                          enable_waiting=False,
                                          enable_routing=False,
                                          progress_function=set_progress)

        set_progress((steps, steps))

        fin = time.time()

        show_dialog_arguments = False
        show_simulation_finished = True
        dropdown_disabled = False
        disable_download = False

        print("Simulation finished")

        traffic_output = add_info_from_mesa_list(sim_traffic, traffic_level_simulation)

        existing_figures = [fig_avg_travel_time, fig_avg_waiting_time, fig_avg_additional_time, fig_hist_waiting_time]
        simulation_name = get_simulation_name(date_hour_dropdown, num_agents, steps, agents_start_method,
                                              agents_end_method, routing_method, respawn_enabled)

        # Analyze and plot simulation data
        (fig_avg_travel_time, fig_avg_waiting_time, fig_avg_additional_time, fig_hist_waiting_time,
         summary_stats_df) = analyze_and_plot_simulation_data(sim_model_data, sim_agent_data, simulation_name,
                                                              existing_figures=existing_figures)

        # Flatten the multiindex DataFrame
        summary_stats_df.columns = summary_stats_df.columns.get_level_values(0)
        summary_stats_df = summary_stats_df.reset_index().rename(columns={"index": "Stat"})

        # Create Bootstrap table from DataFrame
        table = [html.H2("Last simulation's summary statistics", style={'textAlign': 'center'}),
                 dbc.Table.from_dataframe(summary_stats_df, striped=True, bordered=True, hover=True)]

        # STORE THE SIMULATION DATA
        sim_model_data = sim_model_data.reset_index()
        sim_agent_data = sim_agent_data.reset_index()
        data_simulation = {
            'model_data': sim_model_data.to_json(),
            'agent_data': sim_agent_data.to_json()
        }

        set_progress((0, steps))

        print(f"{simulation_name} \t Time: {fin - inicio}")

        return (json.dumps(traffic_output), json.dumps(data_simulation),
                show_dialog_arguments, show_simulation_finished, dropdown_disabled,
                disable_download, disable_download, disable_download,
                fig_avg_travel_time, fig_avg_waiting_time, fig_avg_additional_time, fig_hist_waiting_time,
                table)

    else:
        # Alert the user that no date was selected
        show_dialog_arguments = True
        show_simulation_finished = False
        dropdown_disabled = True
        disable_download = True

    return (traffic_level_simulation_stored, None,
            show_dialog_arguments, show_simulation_finished, dropdown_disabled,
            disable_download, disable_download, disable_download,
            None, None, None, None, None)


@app.callback(
    Output("download-map-simulation", "data"),
    Input("btn-download-map-simulation", "n_clicks"),
    State('traffic-level-simulation-store', 'data'))
def download_simulation_map(n_clicks, traffic_simulation_graph):
    if n_clicks is None:
        return no_update

    # Retrieve DataFrames from Store data
    df = pd.DataFrame(json.loads(traffic_simulation_graph))

    # Convert DataFrames to CSV strings
    csv = df.to_csv()

    return dict(content=csv, filename="simulation_dataframe.csv")


@app.callback(
    Output("download-agent-data-simulation", "data"),
    Input("btn-download-agents-data-simulation", "n_clicks"),
    State('data-simulation-store', 'data'))
def download_simulation_agent_data(n_clicks, simulation_data):
    if n_clicks is None:
        return no_update

    json_data = json.loads(simulation_data)
    agent_data = pd.DataFrame(json.loads(json_data.get("agent_data")))
    csv = agent_data.to_csv()

    return dict(content=csv, filename="simulation_agent_data.csv")


@app.callback(
    Output("download-model-data-simulation", "data"),
    Input("btn-download-model-data-simulation", "n_clicks"),
    State('data-simulation-store', 'data'))
def download_simulation_model_data(n_clicks, simulation_data):
    if n_clicks is None:
        return no_update

    json_data = json.loads(simulation_data)
    model_data = pd.DataFrame(json.loads(json_data.get("model_data")))
    csv = model_data.to_csv()

    return dict(content=csv, filename="simulation_model_data.csv")


if __name__ == '__main__':
    app.run_server()
