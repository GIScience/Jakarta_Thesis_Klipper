# -*- coding: utf-8 -*-
import osmnx as ox
from os import path
from os import listdir, rmdir
from shutil import move
import sys

# user defined parameters
city_name = sys.argv[1]
network_type = sys.argv[2]
network_file_name = sys.argv[3]
output_path = sys.argv[4]

"""Download and save network road graph with OSMnx module."""
ox_graph = ox.graph_from_place(city_name, network_type=network_type)
ox.save_graph_shapefile(ox_graph, network_file_name, output_path)


"""Organise folder structure. Edges and node files will be moved to parent folder."""
graph_folder = path.join(output_path, network_file_name)

for filename in listdir(path.join(graph_folder, 'edges')):
    move(path.join(graph_folder, 'edges', filename), path.join(graph_folder, filename))
rmdir(path.join(graph_folder, 'edges'))

for filename in listdir(path.join(graph_folder, 'nodes')):
    move(path.join(graph_folder, 'nodes', filename), path.join(graph_folder, filename))
rmdir(path.join(graph_folder, 'nodes'))


