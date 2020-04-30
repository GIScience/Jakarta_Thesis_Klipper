# -*- coding: utf-8 -*-
from __init__ import NETWORK_DIR, SETTINGS
from os import path
import geopandas as gpd
import sys
import logging


def join_df(flood_scenario, centrality):
    """"""
    normal_df = gpd.read_file(path.join(NETWORK_DIR, SETTINGS['networks']['normal']))
    flood_df = gpd.read_file(path.join(NETWORK_DIR, SETTINGS['networks'][flood_scenario]))

    if centrality not in normal_df.columns or centrality not in flood_df.columns:
        print('Please first calculate the desired network centrality for the normal and the '
              + flood_scenario + 'scenario.')
        exit()

    df_joined = normal_df.join(flood_df.set_index('osmid'), on='osmid', lsuffix='_normal', rsuffix='_' + flood_scenario)
    df_joined[centrality + '_dif'] = df_joined[centrality + '_' + flood_scenario] - df_joined[centrality + '_normal']

    selected = df_joined[['geometry_normal', 'osmid', centrality + '_dif',
                          centrality + '_normal', centrality + '_' + flood_scenario]]
    geodf = gpd.GeoDataFrame(selected, geometry='geometry_normal')

    return geodf


if __name__ == '__main__':

    flood_scenario_input = None
    centrality_input = None

    try:
        flood_scenario_input = str(sys.argv[1])
    except KeyError:
        logging.error('Please provide one flood scenario, defined in settings.yml > networks, e.g. flooded')
        exit()

    try:
        centrality_input = [str(sys.argv[2])]
        try:
            centrality_input.append(str(sys.argv[3]))
        except IndexError:
            pass
    except IndexError:
        logging.error('Please provide at least one centrality name, e.g. Betweenness, Closeness or both.')
        exit()

    if 'Betweenness' not in centrality_input and 'Closeness' not in centrality_input:
        logging.error('Please provide at least one centrality name, e.g. Betweenness, Closeness or both.')
        exit()

    # run calculation
    for iso_scenario in SETTINGS['networks']:
        if flood_scenario_input != 'normal' and flood_scenario_input == iso_scenario:
            if 'Betweenness' in centrality_input:
                btwn_geodf = join_df(flood_scenario_input, 'btwn')
                btwn_geodf.to_file(path.join(NETWORK_DIR, iso_scenario, 'nodes_btwn_dif.shp'), driver='ESRI Shapefile')

            if 'Closeness' in centrality_input:
                cls_geodf = join_df(flood_scenario_input, 'cls')
                cls_geodf.to_file(path.join(NETWORK_DIR, iso_scenario, 'nodes_cls_dif.shp'), driver='ESRI Shapefile')

            print('Results were saved in', NETWORK_DIR + '/' + iso_scenario + 'nodes_btwn_dif.shp or '
                                                                              'respectively nodes_cls_dif.shp')
