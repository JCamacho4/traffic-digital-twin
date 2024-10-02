import os
from dotenv import load_dotenv

load_dotenv()


MB_TOKEN = os.getenv("MAPBOX_PUBLIC_TOKEN")

SET_UP = {
    "OSMNX_QUERY": 'Málaga, Spain',
    "TILE_LAYER_URL": '//api.mapbox.com/styles/v1/mapbox/light-v11/tiles/{z}/{x}/{y}?access_token=' + MB_TOKEN,
    "TILE_LAYER_SUBDOMAINS": 'abcd',
    "TILE_LAYER_ATTRIBUTION": 'Map tiles by <a href="https://www.mapbox.com/about/maps/">© Mapbox</a><a href="https://www.openstreetmap.org/about/">© OpenStreetMap</a>',
    "MAP_CENTER": [36.7197, -4.4745],
    "MAP_ZOOM": 16,
    "MAP_STYLE": {'width': '100%', 'height': '82vh'},
    "TILE_LAYER_OPACITY": '60%',
}

HIGHWAY_TYPES = ['secondary', 'motorway', 'motorway_link', 'primary', 'tertiary', 'residential', 'primary_link', 'tertiary_link', 'secondary_link', 'unclassified', 'living_street']

MONGO_TOKEN = os.getenv("MONGO_URI")
