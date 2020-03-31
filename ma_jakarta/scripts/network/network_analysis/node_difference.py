# -*- coding: utf-8 -*-
from os import path
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import networkx as nx
import subprocess
import logging
import node_dif_cython


def build_cython():
    """"""
    try:
        cmd = 'python setup.py build_ext --inplace'
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                shell=True)
        return_code = proc.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)

        logging.info('Cython file successfully built.')
    except Exception as err:
        print(err)


def calculate_node_difference(normal_graph, flood_graph, centrality):
    """"""

    # complete/normal graph and flooded/floodprone graph
    # G_normal = nx.read_shp(path.join(BASEDIR, 'graphs_2/complete'))
    g_normal = nx.read_shp(normal_graph)
    node_data_normal = list(g_normal.nodes(data=True))

    # G_flooded = nx.read_shp(path.join(BASEDIR, 'graphs_2/floodprone'))
    g_flood = nx.read_shp(flood_graph)
    node_data_flooded = list(g_flood.nodes(data=True))

    # call cython function to speed up calculation
    centrality_dif = node_dif_cython.centrality_difference(node_data_normal, node_data_flooded, centrality)  # 'btwn'

    # convert coordinates into shapely point geometry for dataframe merge
    for dif in range(len(centrality_dif)):
        centrality_dif[dif][0] = Point(centrality_dif[dif][0])

    # restructure list, filter out item attributes for dataframe
    node_data_flooded_items = []
    for node in range(len(node_data_flooded)):
        node_data_flooded_items.append(node_data_flooded[node][1])

    # attribute names of flood data list
    column_names_flooded = node_data_flooded[0][1].keys()
    # create dataframe out of flood data
    df_flooded = pd.DataFrame(node_data_flooded_items, columns=list(column_names_flooded))
    # create dataframe out of calculated centrality difference data
    df_dif = pd.DataFrame(centrality_dif, columns=['geometry', 'enum_id', 'enum_id_ce', centrality + '_dif'])

    # merge dataframes
    df = df_flooded.merge(df_dif, on='enum_id_ce')
    geodf = gpd.GeoDataFrame(df, geometry='geometry')
    # geodf.to_file(path.join(BASEDIR, 'graphs_2/floodprone/nodes_btwn_dif.shp'), driver='ESRI Shapefile')
    geodf.to_file(path.join(flood_graph, '/nodes_' + centrality + '_dif.shp'), driver='ESRI Shapefile')
