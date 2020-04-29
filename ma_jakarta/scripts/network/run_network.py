# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, NETWORK_DIR, SETTINGS
from ma_jakarta.scripts.network import network_preparation, centrality
import sys
from os import path, mkdir
import networkx as nx
import geopandas as gpd
import logging

scenario = None
acronym = None
chosen_centralities = []

# by user provided arguments
try:
    scenario = str(sys.argv[1])
    chosen_centralities.append(str(sys.argv[2]))
except Exception:
    logging.error('Please provide a graph name and at least one centrality name, e.g. floodprone Betweenness.')
    exit()

# if two centrality arguments are provided by the user; optional argument
try:
    chosen_centralities.append(str(sys.argv[3]))
except IndexError:
    pass

graph_path = str(path.join(NETWORK_DIR, scenario))

if chosen_centralities[0] != 'Betweenness' and chosen_centralities[0] != 'Harmonic_Closeness':
    logging.error('Please choose either Betweenness, Harmonic_Closeness or both as centrality.')
    exit()

# check for layer attribute..
# acronym to check if file already exists
# for centrality_name in chosen_centralities:
#     if centrality_name == 'Betweenness':
#         acronym = 'btwn'
#     elif centrality_name == 'Harmonic_Closeness':
#         acronym = 'cls'

# if centrality is already calculated, exit the script in the beginning
#     if path.isfile(path.join(graph_path, 'nodes_' + acronym + '.shp')):
#         print(path.join(graph_path, 'nodes_' + acronym + '.shp'), 'already exists.')
#         exit()


if scenario != 'normal':
    if not path.exists(path.join(NETWORK_DIR, scenario)):
        mkdir(path.join(NETWORK_DIR, scenario))
        print('Directory', path.join(NETWORK_DIR, scenario), 'created')

        complete_graph = nx.read_shp(path.join(NETWORK_DIR, 'normal'))
        intersect_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS[scenario]))
        # intersect normal graph with flood layer
        network_graph = network_preparation.flood_intersection(complete_graph, graph_path, scenario)
        # TODO: intersect with jakarta border?
    else:
        network_graph = nx.read_shp(graph_path)
else:
    network_graph = nx.read_shp(graph_path)


# create weighted graph for NetworKit centrality calculation
weighted_normal = network_preparation.create_weighted_graph(network_graph)

# calculate centrality
calculated_cent = []
for centrality_name in chosen_centralities:
    calculated_cent.append(centrality.Centrality(graph_path, weighted_normal, network_graph, centrality_name).run())

# if more than one centrality was chosen merge dataframes
if len(calculated_cent) > 1:
    try:
        calculated_cent[0]['btwn'] = calculated_cent[1]['btwn']
    except Exception:
        calculated_cent[0]['cls'] = calculated_cent[1]['cls']

# save as new shapefile
merged_geodf = gpd.GeoDataFrame(calculated_cent[0], geometry='geometry')
merged_geodf.to_file(path.join(graph_path, 'nodes_centrality.shp'), driver='ESRI Shapefile')
# print('Centrality saved:', path.join(graph_path, 'nodes_' + acronym + '.shp'))
