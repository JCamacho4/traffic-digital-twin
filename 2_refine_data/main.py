import os

import networkx as nx

from mapfunctions.split import split_features_from_folder
from mapfunctions.translation import translate_all_files_pairs, mix_tiles_from_two_folder
from mapfunctions.geojson_functions import add_info_to_folder
from mapfunctions.graph_functions import init_graph_bbox, add_traffic_level_from_folder, \
    save_graph, plot_graph_date_filename

import update_data_mongo.dates as mongo_dates
import update_data_mongo.mongo as mongo

import mapfunctions.constants as const
from update_data_mongo.mongo import get_database, insert_data

# =====================================================================================================================
#                       GET THE GRAPH FROM THE FILE, WITH ALL THE NEEDED MODIFICATIONS DONE
# =====================================================================================================================
print("Getting the graph from the file\n\n")
first_execution = False

G = init_graph_bbox(const.GRAPH_BBOX_NORTH, const.GRAPH_BBOX_SOUTH,
                    const.GRAPH_BBOX_EAST, const.GRAPH_BBOX_WEST,
                    osm_ways_to_delete=const.osm_ways_to_delete)

save_graph(G, "graph_output/base_graph")
print("Base graph saved as a file")

if first_execution:
    # We save the nodes and the edges of the graph in MongoDB
    db = get_database("TFG")
    col = db["base_graph"]

    graph_copy = G.copy()

    graph_to_dictionary = nx.node_link_data(graph_copy)
    del graph_to_dictionary['graph']
    del graph_to_dictionary['directed']
    del graph_to_dictionary['multigraph']
    insert_data(col, graph_to_dictionary)
    print("Base graph saved in MongoDB")


# =====================================================================================================================
#              TRANSLATE THE FILES FROM THE TOMTOM API INTO GEOJSON FILES WITH THE CORRECT COORDINATES
# =====================================================================================================================


print("Translating files from the TomTom API into GeoJSON files\n\n")

dir_input_tile_1 = "data/tile1"
dir_input_tile_2 = "data/tile2"

dir_output_tile_1 = "output_pairs/tile1"
dir_output_tile_2 = "output_pairs/tile2"
dir_output_mixed = "output_pairs/mixed"

translate_all_files_pairs(dir_input_tile_1, const.OUTMIN_TILE1, const.OUTMAX_TILE1, dir_output_tile_1)
translate_all_files_pairs(dir_input_tile_2, const.OUTMIN_TILE2, const.OUTMAX_TILE2, dir_output_tile_2)

# Once we got the files for the tiles, we mix them into a single file (each file will have the same name/date)
directories_to_mix = [dir_output_tile_1, dir_output_tile_2, dir_output_mixed]
mix_tiles_from_two_folder(directories_to_mix)


# =====================================================================================================================
#                       ADD INFORMATION TO THE GEOJSON FILES (NEAREST EDGE, SPLITS...)
# =====================================================================================================================


print("Adding information to the GeoJSON files\n\n")

dir_input = "output_pairs/mixed"
dir_output = "output_add_info/mixed"
add_info_to_folder(dir_input, dir_output, G, splits=15)


# =====================================================================================================================
#               WE SPLIT THE GEOJSON FEATURES INTO SMALLER PIECES, SO THE GRAPH EDGES ARE MATCHED
# =====================================================================================================================


print("Splitting the GeoJSON features into smaller pieces\n\n")

dir_input = "output_add_info/mixed"
dir_output = "output_split/mixed"
split_features_from_folder(dir_input, dir_output)

# =====================================================================================================================
#                        ADD INFORMATION TO THE GRAPH (TRAFFIC_FLOW) & SAVE GRAPH IN MONGO
# =====================================================================================================================

print("Adding information to the graph\n\n")

dir_input = "output_split/mixed"
add_traffic_level_from_folder(G, dir_input, precision=3, save_each_graph_mongo=True)

# =====================================================================================================================
#                                    SAVE DATES IN MONGO
# =====================================================================================================================

print("Saving dates in MongoDB\n\n")
mixed_tiles_path = "output_split/mixed"

available_files_info = mongo_dates.get_files_dictionary_from_folder(mixed_tiles_path)
mongo.insert_multiple_data(mongo.get_database()["dates"], available_files_info)

# =====================================================================================================================
#                                         DELETE FILES
# =====================================================================================================================

print("Deleting files\n\n")
dirs = ["data/tile1", "data/tile2", "output_pairs/tile1", "output_pairs/tile2", "output_pairs/mixed", "output_add_info/mixed", "output_split/mixed"]

for directory in dirs:
    for filename in os.listdir(directory):
        os.remove(f"{directory}/{filename}")


# =====================================================================================================================
#                                               SAVE THE GRAPH
# =====================================================================================================================

# print("Saving the graph\n\n")
#
# save_graph(G, "graph_output/traffic_15files_reduced")

# =====================================================================================================================
#                                       PLOT THE GRAPH WITH ALL THE DATES
# =====================================================================================================================


# for filename in os.listdir("output_split/mixed"):
#     if filename.endswith(".json"):
#         plot_graph_date_filename(G, filename, size=30)
#         pass
