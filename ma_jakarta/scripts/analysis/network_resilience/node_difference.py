# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from os import path
import geopandas as gpd
import sys
import logging


def centrality_change(normal_df, flooded_df, centrality):
    """Calculates absolute centrality change of each node"""
    if centrality not in normal_df.columns or centrality not in flooded_df.columns:
        print('Please first calculate the desired network centrality for the normal and the flooded scenario.')
        exit()

    df_joined = normal_df.join(flooded_df.set_index('osmid'), on='osmid', lsuffix='_n', rsuffix='_f')
    df_joined[centrality + '_dif'] = df_joined[centrality + '_f'] - df_joined[centrality + '_n']

    selected = df_joined[['geometry_n', 'osmid', centrality + '_dif', centrality + '_n', centrality + '_f']]
    geodf = gpd.GeoDataFrame(selected, geometry='geometry_n')

    return geodf


def rel_centrality_change(normal_df, flooded_df, centrality):
    """Calculates relative centrality change of each node -> not applied"""

    df_joined = normal_df.join(flooded_df.set_index('osmid'), on='osmid', lsuffix='_normal', rsuffix='_f')
    df_joined[centrality + '_r_ch'] = df_joined[centrality + '_n'] / df_joined[centrality + '_f']

    selected = df_joined[['geometry_n', 'osmid', centrality + '_r_ch',
                          centrality + '_n', centrality + '_f']]
    geodf = gpd.GeoDataFrame(selected, geometry='geometry_n')

    return geodf


if __name__ == '__main__':

    centrality_input = None

    try:
        centrality_input = [str(sys.argv[1])]
        try:
            centrality_input.append(str(sys.argv[2]))
        except IndexError:
            pass
    except IndexError:
        logging.error('Please provide at least one centrality name, e.g. Betweenness, Closeness or both.')
        exit()

    if 'Betweenness' not in centrality_input and 'Closeness' not in centrality_input:
        logging.error('Please provide at least one centrality name, e.g. Betweenness, Closeness or both.')
        exit()

    normal_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['networks']['normal']))
    flooded_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['networks']['flooded']))

    # run calculation
    if 'Betweenness' in centrality_input:
        btwn_geodf = centrality_change(normal_data, flooded_data, 'btwn')
        btwn_geodf.to_file(path.join(DATA_DIR, SETTINGS['networks']['btwn_dif']), driver='ESRI Shapefile')
        print('Results saved in:', DATA_DIR, SETTINGS['networks']['btwn_dif'])

    if 'Closeness' in centrality_input:
        cls_geodf = centrality_change(normal_data, flooded_data, 'cls')
        cls_geodf.to_file(path.join(DATA_DIR, SETTINGS['networks']['cls_dif']), driver='ESRI Shapefile')
        print('Results saved in:', DATA_DIR, SETTINGS['networks']['cls_dif'])
