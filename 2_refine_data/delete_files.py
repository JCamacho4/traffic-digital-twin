import os

dirs = ["data/tile1", "data/tile2", "output_pairs/tile1", "output_pairs/tile2", "output_pairs/mixed", "output_add_info/mixed", "output_split/mixed"]
for directory in dirs:
    for filename in os.listdir(directory):
        os.remove(f"{directory}/{filename}")