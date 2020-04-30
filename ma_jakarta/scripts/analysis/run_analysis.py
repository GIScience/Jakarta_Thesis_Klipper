# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from ma_jakarta.scripts.analysis import reached_values, histogram
from ma_jakarta.scripts.analysis import impact_maps
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from os import path, mkdir
import sys
import logging


# user defined analysis methods
analysis_choise = None
try:
    analysis_choise = [str(sys.argv[1])]
    try:
        analysis_choise.append(str(sys.argv[2]))
    except IndexError:
        pass
except IndexError:
    logging.error('Please provide at least on analysis method, e.g. impact_maps, histogram or both.')
    exit()

union_area_dict = {}
union_pop_dict = {}
union_node_dict = []
union_btwn_dict = []
union_cls_dict = []

normal_punched = None
flood_punched = []

# preprocessing
for iso_scenario in SETTINGS['reached']:
    if iso_scenario == 'normal':
        normal_scenario = gpd.read_file(path.join(DATA_DIR, SETTINGS['reached'][iso_scenario]))
        modified_layer = reached_values.dissolve_layer(normal_scenario)

        if 'impact_maps' in analysis_choise:
            normal_punched = impact_maps.punch_layer(modified_layer, iso_scenario)
    else:
        scenario_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['reached'][iso_scenario]))
        union_layer = reached_values.dissolve_layer(scenario_layer)
        modified_layer = reached_values.flood_difference(union_layer, iso_scenario)

        if 'impact_maps' in analysis_choise:
            punched_layer = impact_maps.punch_layer(modified_layer, iso_scenario)
            flood_punched.append(punched_layer)

    if 'histogram' in analysis_choise:
        # histogram
        union_area_dict[iso_scenario] = {}
        union_area = reached_values.reached_area(modified_layer)
        union_area_dict[iso_scenario].update(union_area)

        union_pop_dict[iso_scenario] = {}
        union_pop = reached_values.reached_pop(modified_layer)
        union_pop_dict[iso_scenario].update(union_pop)

        union_node, union_btwn, union_cls = reached_values.reached_nodes(modified_layer, iso_scenario)
        union_node_dict.append(union_node)
        union_btwn_dict.append(union_btwn)
        union_cls_dict.append(union_cls)


if 'impact_maps' in analysis_choise:

    # create output directory
    if not path.exists(path.join(DATA_DIR, 'results/impact_maps')):
        mkdir(path.join(DATA_DIR, 'results/impact_maps'))

    # merge multiple flood dataframes to one for better handeling
    flood_merged = pd.concat([layer for layer in flood_punched])

    if normal_punched is not None and len(flood_punched) != 0:
        for iso_scenario in SETTINGS['reached']:
            if iso_scenario != 'normal':
                # calculate access change maps for each flood scenario
                flood_geodf = flood_merged.loc[flood_merged['scenario'] == iso_scenario]
                impact_maps.union_access(normal_punched, flood_geodf, iso_scenario)

    print('Results for impact maps were saved in', DATA_DIR + '/results/impact_maps')


# TODO: rename to e.g. plots?
if 'histogram' in analysis_choise:

    # create output directories
    if not path.exists(path.join(DATA_DIR, 'results/plots')):
        mkdir(path.join(DATA_DIR, 'results/plots'))

    if not path.exists(path.join(DATA_DIR, 'results/tables')):
        mkdir(path.join(DATA_DIR, 'results/tables'))

    # define amount of rows and columns depending on amount of user defined amenities
    nrows = None
    ncols = None

    if len(SETTINGS['amenity_osm_values']) == 1:
        nrows = 1
        ncols = 1
    elif len(SETTINGS['amenity_osm_values']) == 2:
        nrows = 1
        ncols = 2
    elif len(SETTINGS['amenity_osm_values']) == 3 or len(SETTINGS['amenity_osm_values']) == 4:
        nrows = 2
        ncols = 2
    elif len(SETTINGS['amenity_osm_values']) == 5 or len(SETTINGS['amenity_osm_values']) == 6:
        nrows = 2
        ncols = 3
    elif len(SETTINGS['amenity_osm_values']) == 7 or len(SETTINGS['amenity_osm_values']) == 8 or \
            len(SETTINGS['amenity_osm_values']) == 9:
        nrows = 3
        ncols = 3

    # create plot for reached area
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 10))
    for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
        histogram.create_histogram(union_area_dict, amenity, ax, 'Reached Area [km2]', 'area', 1e-6)
    plt.tight_layout()
    plt.savefig(path.join(DATA_DIR, 'results/plots/reached_area_union.png'))

    # create plot for reached population
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 10))
    for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
        histogram.create_histogram(union_pop_dict, amenity, ax, 'Reached Population [mil]', 'population', 1e-6)
    plt.tight_layout()
    plt.savefig(path.join(DATA_DIR, 'results/plots/reached_pop_union.png'))

    # create csv files for reached nodes and centralities
    node_merged = pd.concat([layer for layer in union_node_dict])
    node_merged.to_csv(path.join(DATA_DIR, 'results/tables/reached_nodes_union.csv'))

    btwn_merged = pd.concat([layer for layer in union_btwn_dict])
    btwn_merged.to_csv(path.join(DATA_DIR, 'results/tables/reached_btwn_union.csv'))

    cls_merged = pd.concat([layer for layer in union_cls_dict])
    cls_merged.to_csv(path.join(DATA_DIR, 'results/tables/reached_cls_union.csv'))

    print('Results for histograms and tables were saved in', DATA_DIR + '/results/tables and ',
          DATA_DIR + '/results/plots')
