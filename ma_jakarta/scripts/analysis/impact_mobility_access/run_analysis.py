# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from ma_jakarta.scripts.analysis.impact_mobility_access import histogram, impact_maps, reached_values
from ma_jakarta.scripts.data_preprocessing import admin_border
import geopandas as gpd
import fiona as fn
import pandas as pd
import matplotlib.pyplot as plt
from os import path, mkdir
import sys
import logging


if __name__ == '__main__':

    # user defined analysis methods
    analysis_choice = None
    try:
        analysis_choice = [str(sys.argv[1])]
        try:
            analysis_choice.append(str(sys.argv[2]))
        except IndexError:
            pass
    except IndexError:
        logging.error('Please provide at least on analysis method, e.g. impact_maps, histogram or both.')
        exit()

    normal_scenario_punched = None
    flooded_scenario_punched = []
    city_area = None
    city_pop = None
    union_area_dict = {}
    union_pop_dict = {}

    # input data
    city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))
    flood_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed']))
    pop_raster = path.join(DATA_DIR, SETTINGS['population']['extract'])

    # preprocessing
    for iso_scenario in SETTINGS['isochrones']:
        if iso_scenario == 'normal':
            normal_scenario = gpd.read_file(path.join(DATA_DIR, SETTINGS['isochrones'][iso_scenario]))
            modified_layer = reached_values.dissolve_layer(normal_scenario)

            if 'impact_maps' in analysis_choice:
                normal_scenario_punched = impact_maps.punch_layer(modified_layer, iso_scenario)
        else:
            scenario_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['isochrones'][iso_scenario]))
            modified_layer = reached_values.dissolve_layer(scenario_layer)

            if 'impact_maps' in analysis_choice:
                punched_layer = impact_maps.punch_layer(modified_layer, iso_scenario)
                flooded_scenario_punched.append(punched_layer)

        if 'histogram' in analysis_choice:
            with fn.open(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed'])) as city_border_fn:
                city_area = reached_values.total_city_area(city_border_fn)
                city_pop = reached_values.total_city_pop(pop_raster, city_border_fn)

            intersected_layer = admin_border.border_intersect(city_border, modified_layer)

            union_area_dict[iso_scenario] = {}
            union_area = reached_values.reached_area(intersected_layer)
            union_area_dict[iso_scenario].update(union_area)

            union_pop_dict[iso_scenario] = {}
            union_pop = reached_values.reached_pop(pop_raster, intersected_layer)
            union_pop_dict[iso_scenario].update(union_pop)

    if 'impact_maps' in analysis_choice:

        # create output directory
        if not path.exists(path.join(DATA_DIR, SETTINGS['impact_access']['path_maps'])):
            mkdir(path.join(DATA_DIR, SETTINGS['impact_access']['path_maps']))
            print('Folder', path.join(DATA_DIR, SETTINGS['impact_access']['path_maps']), 'created.')

        # merge multiple flood dataframes to one for better handeling
        flooded_scenario_merged_df = pd.concat([layer for layer in flooded_scenario_punched])

        if normal_scenario_punched is not None and len(flooded_scenario_punched) != 0:
            for iso_scenario in SETTINGS['isochrones']:
                if iso_scenario != 'normal':
                    # calculate access change maps for each flood scenario
                    flooded_scenario_merged = flooded_scenario_merged_df.loc[
                        flooded_scenario_merged_df['scenario'] == iso_scenario]

                    for amenity in SETTINGS['amenity_osm_values']:
                        impact_map_result = impact_maps.union_access(normal_scenario_punched, flooded_scenario_merged,
                                                                     amenity, city_border, flood_layer)

                        impact_map_result.to_file(path.join(DATA_DIR,
                                                            SETTINGS['impact_access']['path_maps'],
                                                            'access_dif_' + iso_scenario + '_' + amenity + '.shp'),
                                                  driver='ESRI Shapefile')
                        print(path.join(DATA_DIR, SETTINGS['impact_access']['path_maps'],
                                        'access_dif_' + iso_scenario + '_' + amenity + '.shp'), 'saved.')

    if 'histogram' in analysis_choice:

        # create output directories
        if not path.exists(path.join(DATA_DIR, SETTINGS['impact_access']['path_histogram'])):
            mkdir(path.join(DATA_DIR, SETTINGS['impact_access']['path_histogram']))
            print('Folder', path.join(DATA_DIR, SETTINGS['impact_access']['path_histogram']), 'created.')

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

        # create plot for reached area
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 6))
        for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
            histogram.create_histogram(city_area, union_area_dict, amenity, ax, 'Reached Area [km2]', 'area', 1e-6)
        plt.tight_layout()

        plt.savefig(path.join(DATA_DIR, SETTINGS['impact_access']['path_histogram'], 'reached_area_union.png'))
        print(path.join(DATA_DIR, SETTINGS['impact_access']['path_histogram'], 'reached_area_union.png'), 'saved')

        # create plot for reached population
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 6))
        for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
            if city_pop >= 1000000:
                histogram.create_histogram(city_pop, union_pop_dict, amenity, ax,
                                           'Reached Population [mil]', 'population', 1e-6)
            else:
                histogram.create_histogram(city_pop, union_pop_dict, amenity, ax, 'Reached Population', 'population', 1)
        plt.tight_layout()

        plt.savefig(path.join(DATA_DIR, SETTINGS['impact_access']['path_histogram'], 'reached_pop_union.png'))
        print(path.join(DATA_DIR, SETTINGS['impact_access']['path_histogram'], 'reached_pop_union.png'), 'saved.')
