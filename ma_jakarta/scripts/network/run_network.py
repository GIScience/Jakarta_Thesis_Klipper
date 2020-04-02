# -*- coding: utf-8 -*-
from __init__ import BASEDIR, DATA_DIR, NETWORK_DIR, SETTINGS
from ma_jakarta.scripts.network import network_preparation
from ma_jakarta.scripts.network.network_analysis import centrality
import sys
from os import path, mkdir
import networkx as nx
import geopandas as gpd
import logging

# by user provided arguments
try:
    graph_name = str(sys.argv[1])
    graph_path = str(path.join(NETWORK_DIR, graph_name))
    centrality_name = str(sys.argv[2])
except Exception:
    logging.error('Please provide a graph name and at least one centrality name, e.g. floodprone Betweenness.')
    exit()

if centrality_name != 'Betweenness' and centrality_name != 'Harmonic_Closeness':
    logging.error('Please choose either Betweenness, Harmonic_Closeness or both as centrality.')
    exit()


# declaration to check if file already exists
declaration = None
if centrality_name == 'Betweenness':
    declaration = 'btwn'
elif centrality_name == 'Harmonic_Closeness':
    declaration = 'cls'

# if centrality is already calculated, exit the script in the beginning
if path.isfile(path.join(graph_path, 'node_' + declaration + '.shp')):
    print(path.join(graph_path, 'node_' + declaration + '.shp'), 'already exists.')
    exit()


if graph_name != 'normal':
    if not path.exists(path.join(NETWORK_DIR, graph_name)):
        mkdir(path.join(NETWORK_DIR, graph_name))
        print('Directory', path.join(NETWORK_DIR, graph_name), 'created')

        complete_graph = nx.read_shp(path.join(NETWORK_DIR, 'normal'))
        intersect_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS[graph_name]))
        # intersect normal graph with intersection layer
        network_graph = network_preparation.flood_intersection(complete_graph, intersect_layer, graph_path)
    else:
        network_graph = nx.read_shp(graph_path)
else:
    network_graph = nx.read_shp(graph_path)


# create weighted graph for NetworKit centrality calculation
weighted_normal = network_preparation.create_weighted_graph(network_graph)

# calculate centrality
centrality.Centrality(graph_path, weighted_normal, network_graph, centrality_name).run()
print('Centrality saved:', path.join(graph_path, 'node_' + declaration + '.shp'))


# if two centrality arguments are provided by the user; optional argument
try:
    second_centrality_name = str(sys.argv[3])

    second_declaration = None
    if second_centrality_name == 'Betweenness':
        second_declaration = 'btwn'
    elif second_centrality_name == 'Harmonic_Closeness':
        second_declaration = 'cls'

    if not path.isfile(path.join(graph_path, 'node_' + second_declaration + '.shp')):
        centrality.Centrality(graph_path, weighted_normal, network_graph, second_centrality_name).run()
        print('Centrality saved:', path.join(graph_path, 'node_' + second_declaration + '.shp'))
    else:
        print(path.join(graph_path, 'node_' + second_declaration + '.shp'), 'already exists.')
except IndexError:
    pass
