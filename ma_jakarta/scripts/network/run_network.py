# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, NETWORK_DIR, SETTINGS
from ma_jakarta.scripts.network import network_preparation, centrality
from os import path, mkdir
import networkx as nx
import geopandas as gpd
import logging
import sys

if __name__ == '__main__':

    scenario = None
    acronym = None
    chosen_centralities = []

    # by user provided arguments
    try:
        scenario = str(sys.argv[1])
        chosen_centralities.append(str(sys.argv[2]))
    except IndexError:
        logging.error('Please provide a graph name and at least one centrality name, e.g. normal Betweenness.')
        sys.exit(1)

    # if two centrality arguments are provided by the user; optional argument
    try:
        chosen_centralities.append(str(sys.argv[3]))
    except IndexError:
        pass

    graph_path = str(path.join(NETWORK_DIR, scenario))
    centrality_path = str(path.join(DATA_DIR, SETTINGS['networks']['path'], scenario))
    if not path.exists(path.join(DATA_DIR, SETTINGS['networks']['path'])):
        mkdir(path.join(DATA_DIR, SETTINGS['networks']['path']))
        print('Directory', path.join(DATA_DIR, SETTINGS['networks']['path']), 'created')
    if not path.exists(centrality_path):
        mkdir(path.join(centrality_path))
        print('Directory', centrality_path, 'created')

    if chosen_centralities[0] != 'Betweenness' and chosen_centralities[0] != 'Closeness':
        logging.error('Please choose either Betweenness, Closeness or both as centrality methods.')
        sys.exit(1)

    if scenario != 'normal':
        if not path.exists(graph_path):
            mkdir(graph_path)
            print('Directory', graph_path, 'created')

            # intersect normal graph with flood layer
            complete_graph = nx.read_shp(path.join(NETWORK_DIR, 'normal')).copy()
            network_preparation.remove_flood_data(complete_graph, graph_path)
            # clean graph from existing centrality
            network_preparation.clean_node_file(scenario)
            # load data as network graph
            network_graph = nx.read_shp(graph_path)
        else:
            network_graph = nx.read_shp(graph_path)
    else:
        network_graph = nx.read_shp(graph_path)

    # create weighted graph for NetworKit centrality calculation
    weighted_normal = network_preparation.create_weighted_graph(network_graph)

    # calculate centrality
    calculated_cent = []
    for centrality_name in chosen_centralities:
        calculated_cent.append(centrality.Centrality(graph_path, weighted_normal, network_graph, centrality_name, scenario).run())

    # if more than one centrality was chosen, merge dataframes
    if len(calculated_cent) > 1:
        try:
            calculated_cent[0]['btwn'] = calculated_cent[1]['btwn']
        except Exception:
            calculated_cent[0]['cls'] = calculated_cent[1]['cls']

    # save as new shapefile
    merged_geodf = gpd.GeoDataFrame(calculated_cent[0], geometry='geometry')
    merged_geodf.to_file(path.join(DATA_DIR, SETTINGS['networks'][scenario]), driver='ESRI Shapefile')
    print('Centrality saved:', path.join(DATA_DIR, SETTINGS['networks'][scenario]))
