# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from ma_jakarta.scripts.data_preprocessing import admin_border
from os import path, mkdir
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, mapping
import fiona as fn
import sys
import logging


def create_grid():
    """Creates grid for city area with 1 x 1 square kilometer cell size"""
    xmin, ymin, xmax, ymax = fn.open(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed'])).bounds
    grid_width = 0.009039
    grid_height = 0.009039
    rows = (ymax - ymin) / grid_height
    cols = (xmax - xmin) / grid_width
    ring_xleft_origin = xmin
    ring_xright_origin = xmin + grid_width
    ring_ytop_origin = ymax
    ring_ybottom_origin = ymax - grid_height
    counter = 1
    schema = {'geometry': 'Polygon', 'properties': {'grid_id': 'int'}}
    with fn.open(path.join(DATA_DIR, SETTINGS['data_distribution']['grid']), 'w', 'ESRI Shapefile', schema) as c:
        for i in np.arange(cols):
            ring_ytop = ring_ytop_origin
            ring_ybottom = ring_ybottom_origin
            for j in np.arange(rows):
                polygon = Polygon(
                    [(ring_xleft_origin, ring_ytop), (ring_xright_origin, ring_ytop),
                     (ring_xright_origin, ring_ybottom), (ring_xleft_origin, ring_ybottom)])
                c.write({'geometry': mapping(polygon), 'properties': {'grid_id': counter}})
                counter += 1
                ring_ytop = ring_ytop - grid_height
                ring_ybottom = ring_ybottom - grid_height
            ring_xleft_origin = ring_xleft_origin + grid_width
            ring_xright_origin = ring_xright_origin + grid_width


def health_location(df_input, grid_poly, scenario, id_name):
    """Calculates health site amount per square kilometer"""

    # count amenities for each cell
    df_distribution = df_input.groupby('grid_id_en')[id_name].count().to_frame()

    df_grid_dist = pd.merge(grid_poly['grid_id_en'], df_distribution, on='grid_id_en', how='outer', indicator=True)
    # add grid cells without any health locations
    df_grid_dist_complete = df_grid_dist.merge(grid_poly, on='grid_id_en')
    df_result_dist = df_grid_dist_complete[['grid_id_en', id_name, 'geometry']].copy()

    # calculate change
    if scenario != 'normal':
        if not path.exists(path.join(DATA_DIR, SETTINGS['data_distribution']['health_location']['normal'])):
            print('Please run first for normal scenario')
            sys.exit()
        else:
            hs_normal = gpd.read_file(path.join(DATA_DIR, SETTINGS['data_distribution']['health_location']['normal']))

            # calculate distribution change
            dist_joined = hs_normal.join(df_result_dist.set_index('grid_id_en'),
                                         on='grid_id_en', rsuffix='_' + scenario)
            dist_joined['hs_dif'] = dist_joined[id_name + '_' + scenario] - dist_joined[id_name]
            dist_joined.loc[(dist_joined[id_name].notnull()) &
                            (dist_joined[id_name + '_' + scenario].isnull()), 'hs_dif'] = -dist_joined[id_name]

            df_result_dist = dist_joined[['geometry', 'grid_id_en', 'hs_dif', id_name, id_name + '_' + scenario]]

    return df_result_dist


def bed_capacity(df_input, grid_poly, scenario):
    """Calculates bed amount per square kilometer"""

    # sum up bed amount for each cell
    df_sum = df_input.groupby('grid_id_en')['cap_int'].sum().to_frame()

    df_grid_bed = pd.merge(grid_poly['grid_id_en'], df_sum, on='grid_id_en', how='outer', indicator=True)
    # add grid cells without any capacity
    df_grid_bed_complete = df_grid_bed.merge(grid_poly, on='grid_id_en')

    df_result_cap = df_grid_bed_complete[['grid_id_en', 'cap_int', 'geometry']]

    # calculate change
    if scenario != 'normal':
        if not path.exists(path.join(DATA_DIR, SETTINGS['data_distribution']['bed_capacity']['normal'])):
            print('Please run first for normal scenario')
            exit()
        else:
            cap_normal = gpd.read_file(path.join(DATA_DIR, SETTINGS['data_distribution']['bed_capacity']['normal']))

            # calculate capacity change
            cap_joined = cap_normal.join(df_result_cap.set_index('grid_id_en'), on='grid_id_en', rsuffix='_' + scenario)
            cap_joined['cap_dif'] = cap_joined['cap_int_' + scenario] - cap_joined['cap_int']
            cap_joined.loc[(cap_joined.cap_int.notnull()) &
                           (cap_joined['cap_int_' + scenario].isnull()), 'cap_dif'] = -cap_joined['cap_int']

            df_result_cap = cap_joined[['geometry', 'grid_id_en', 'cap_dif', 'cap_int', 'cap_int_' + scenario]]

    return df_result_cap


def calculate_supply(grid_poly, amenities, scenario, analysis_types):
    """Calculates available health supply for each grid cell"""

    df_result = None
    path_name = None

    # spatial join to receive information about HS per grid cell
    gdf_joined = gpd.sjoin(amenities, grid_poly, how="left", op='within')

    for analysis_type in analysis_types:
        if analysis_type == 'health_location':

            if not path.exists(path.join(DATA_DIR, SETTINGS['data_distribution']['health_location']['path'])):
                mkdir(path.join(DATA_DIR, SETTINGS['data_distribution']['health_location']['path']))

            # osm data id = id_1; hot data id = osm_id
            id_name = ['id_1' if 'id_1' in gdf_joined else 'osm_id'][0]

            df_selected = gdf_joined[['grid_id_en', id_name, 'geometry']]

            df_result = health_location(df_selected, grid_poly, scenario, id_name)
            path_name = path.join(DATA_DIR, SETTINGS['data_distribution']['health_location'][scenario])

        elif analysis_type == 'bed_capacity':

            if 'cap_int' in gdf_joined:

                if not path.exists(path.join(DATA_DIR, SETTINGS['data_distribution']['bed_capacity']['path'])):
                    mkdir(path.join(DATA_DIR, SETTINGS['data_distribution']['bed_capacity']['path']))

                df_selected = gdf_joined[['grid_id_en', 'cap_int', 'geometry']]

                df_result = bed_capacity(df_selected, grid_poly, scenario)
                path_name = path.join(DATA_DIR, SETTINGS['data_distribution']['bed_capacity'][scenario])

            else:
                print("No capacity data provided. If data exists, please rename the column to 'cap_int'.")
                sys.exit()

        geodf = gpd.GeoDataFrame(df_result, geometry='geometry')
        geodf.to_file(path_name, driver='ESRI Shapefile')
        print('Result saved: ' + path_name)


if __name__ == '__main__':

    scenario_name = None
    hs_analysis_list = []

    try:
        scenario_name = str(sys.argv[1])
    except KeyError:
        logging.error('Please provide one scenario name, defined in settings.yml > networks, e.g. normal or flooded')
        exit()

    try:
        hs_analysis_list.append(str(sys.argv[2]))

        try:
            hs_analysis_list.append(str(sys.argv[3]))
        except IndexError:
            pass
    except KeyError:
        logging.error('Please provide at least one analysis calculation, e.g., health_location or bed_capacity.')
        exit()

    # input data
    amenity_input = gpd.read_file(path.join(DATA_DIR, SETTINGS['amenities'][scenario_name]))

    if not path.exists(path.join(DATA_DIR, SETTINGS['data_distribution']['grid'])):
        print('Grid file does not exists and will be first created.')
        create_grid()

    # intersect grid with city border
    city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))
    grid_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['data_distribution']['grid']))
    grid_intersected = admin_border.border_intersect(city_border, grid_layer)

    # second enumeration due to the case when border_intersection creates multipart polygon
    # -> each cell part receives own id
    grid_intersected.insert(0, 'grid_id_en', range(len(grid_intersected)))

    # run supply calculation
    calculate_supply(grid_intersected, amenity_input, scenario_name, hs_analysis_list)
