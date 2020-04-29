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
        print(
            'Please first calculate the desired network centrality for the normal and the ' + flood_scenario + 'scenario.')
        exit()

    df_joined = normal_df.join(flood_df.set_index('osmid'), on='osmid', lsuffix='_normal', rsuffix='_' + flood_scenario)
    df_joined[centrality + '_dif'] = df_joined[centrality + '_' + flood_scenario] - df_joined[centrality + '_normal']

    selected = df_joined[['geometry_normal', 'osmid', centrality + '_dif',
                          centrality + '_normal', centrality + '_' + flood_scenario]]
    geodf = gpd.GeoDataFrame(selected, geometry='geometry_normal')
    geodf.to_file(path.join(NETWORK_DIR, flood_scenario, 'nodes_' + centrality + '_dif.shp'), driver='ESRI Shapefile')
    print(path.join(NETWORK_DIR, flood_scenario, 'nodes_' + centrality + '_dif.shp') + ' saved')


if __name__ == '__main__':

    try:
        flood_scenario_input = SETTINGS['networks'][sys.argv[1]]
    except KeyError:
        logging.error('Please provide one flood scenario, defined in settings.yml > networks, e.g. flooded')
        flood_scenario_input = None
        exit()

    centrality_input = sys.argv[2]
    try:
        second_centrality_input = sys.argv[3]
    except IndexError:
        second_centrality_input = None
        pass

    if centrality_input != 'Betweenness' and second_centrality_input != 'Betweenness' and centrality_input != 'Closeness' and second_centrality_input != 'Closeness':
        logging.error('Please provide at least one centrality name, e.g. Betweenness, Closeness or both.')
        exit()

    # run calculation
    for iso_scenario in SETTINGS['networks']:
        if flood_scenario_input != 'normal' and flood_scenario_input == iso_scenario:
            if centrality_input == 'Betweenness' or second_centrality_input == 'Betweenness':
                join_df(flood_scenario_input, 'btwn')
            if centrality_input == 'Closeness' or second_centrality_input == 'Closeness':
                join_df(flood_scenario_input, 'cls')
