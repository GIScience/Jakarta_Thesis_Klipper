# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
import osmnx as ox
import geopandas as gpd
from os import path
from os import listdir, rmdir
from shutil import move
import sys

if __name__ == '__main__':
    # user defined parameters
    city_input = sys.argv[1]
    network_type = sys.argv[2]
    network_file_name = sys.argv[3]
    output_path = sys.argv[4]

    # Download and save network road graph with OSMnx module
    if '.shp' in city_input or '.geojson' in city_input:
        # download data for given shapefile
        city_shp = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))
        city_polygon = city_shp['geometry'].loc[0]
        ox_graph = ox.graph_from_polygon(city_polygon, network_type=network_type)
    else:
        # download data for given city name, e.g. 'Berlin, Germany'
        ox_graph = ox.graph_from_place(city_input, network_type=network_type)

    ox.save_graph_shapefile(ox_graph, network_file_name, output_path)

    # Organise folder structure. Edge and node files will be moved to parent folder
    graph_folder = path.join(output_path, network_file_name)

    for filename in listdir(path.join(graph_folder, 'edges')):
        move(path.join(graph_folder, 'edges', filename), path.join(graph_folder, filename))
    rmdir(path.join(graph_folder, 'edges'))

    for filename in listdir(path.join(graph_folder, 'nodes')):
        move(path.join(graph_folder, 'nodes', filename), path.join(graph_folder, filename))
    rmdir(path.join(graph_folder, 'nodes'))

    print(network_file_name, 'graph data saved in:', graph_folder)


