# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from ma_jakarta.scripts.data_preprocessing import admin_border
from os import path, mkdir
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, mapping, LineString, shape
import sys
import logging
from shapely.ops import unary_union, polygonize
from rasterstats import zonal_stats
from area import area


def add_capacity_data(scenario, amenity_type, range_value):
    """Adds health capacity attributes to isochrones"""
    iso_layer = None

    # load isochrone data and sort by amenity type and range value
    if scenario == 'normal':
        iso_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['isochrones'][scenario]))
    elif scenario == 'flooded':
        iso_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['isochrones']['pre_' +scenario]))
    iso_hosp = iso_layer.loc[iso_layer.amenity == amenity_type].copy()
    iso_hosp_value = iso_hosp.loc[iso_hosp.value == range_value].copy()

    # load health amenity data and sort by amenity type
    hs_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['amenities'][scenario]))
    # osm data id = id_1; hot data id = osm_id
    id_name = ['id_1' if 'id_1' in hs_layer else 'osm_id'][0]
    hs_hosp = hs_layer.loc[hs_layer.amenity == amenity_type].copy()
    hs_hosp = hs_hosp.rename({id_name: "amenity_id"}, axis=1)

    # merge data
    data_merged = pd.merge(hs_hosp, iso_hosp_value, on='amenity_id')
    data_merged = data_merged.rename({"geometry_y": "geometry"}, axis=1)

    data_selected = data_merged[['geometry', 'amenity_id', 'cap_int']]

    return data_selected


def create_boundaries(input_layer):
    """Generates overlay layer containing all possible polygons of overlapping isochrones.
    It considers only the isochrone boundaries, not the number of overlapping polygons"""

    # generate linestring layer containing the exterior coordinates of the isochrone boundaries
    boundaries = [LineString(list(shape(geom).exterior.coords)) for geom in input_layer['geometry']]
    # dissolve linestring connections to result in single linestring segments
    unioned_data = unary_union(boundaries)
    # generate polygons using linestring segments as boundary -> isochrone fragments
    polygonized_data = [geom for geom in polygonize(unioned_data)]

    layer_list = []
    for i, pol in enumerate(polygonized_data):
        layer_list.append(pd.DataFrame.from_dict({'geometry': mapping(pol)['coordinates']}))

    concat_df = pd.concat([layer for layer in layer_list]).reset_index()
    concat_df['geometry'] = [Polygon(g) for g in concat_df['geometry']]

    result_geodf = gpd.GeoDataFrame(concat_df, geometry='geometry')

    return result_geodf


def intersect_overlap(scenario, iso_capacities, iso_boundaries):
    """Amount of overlapping isochrone fragments result in specific available health capacity within each area"""
    geom_list = []
    counter = 0

    # for each polygon respectively isochrone fragment
    for overlay_idx in range(len(iso_boundaries)):

        original_idx_overlapping = 0
        cap_int_value = 0  # counter to sum up cumulative health capacity for overlapping areas
        overlay_idx_geom = iso_boundaries.geometry[overlay_idx]

        # for each isochrone
        for original_idx in range(len(iso_capacities)):

            original_idx_geom = iso_capacities.geometry[original_idx]

            if overlay_idx_geom.intersects(original_idx_geom):
                intersected_geom = overlay_idx_geom.intersection(original_idx_geom)

                if intersected_geom.geom_type == 'Polygon':

                    # sum up bed capacity per geometry
                    cap_int_value += iso_capacities.cap_int[original_idx]
                    counter += 1
                    original_idx_overlapping = original_idx_overlapping + 1

                    if len(geom_list) == 0:
                        geom_list.append([counter, original_idx_overlapping, cap_int_value, intersected_geom])
                    else:
                        # drop geometries with an area size smaller than 1m²
                        if area(mapping(intersected_geom)) > 0.000009039:
                            # drop overlapping rows
                            if intersected_geom.almost_equals(geom_list[-1][3]):
                                del geom_list[-1]
                                geom_list.append([counter, original_idx_overlapping, cap_int_value, intersected_geom])
                            else:
                                geom_list.append([counter, original_idx_overlapping, cap_int_value, intersected_geom])

    df = pd.DataFrame(geom_list, columns=['counter', 'overlap', 'cap_int', 'geometry'])
    result_geodf = gpd.GeoDataFrame(df, geometry='geometry')

    if scenario != 'normal':
        # remove flooded areas
        flood_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed']))
        result_geodf = gpd.overlay(result_geodf, flood_layer, how='symmetric_difference')

    # drop entries with missing and empty geometries
    result_geodf = result_geodf[~(result_geodf['geometry'].is_empty | result_geodf['geometry'].isna())]

    return result_geodf


def drop_similar_entries(poly_layer=None):
    """Removes duplicate geometries"""
    poly_list = []

    # select still overlapping geometries
    for poly_idx in range(len(poly_layer[:-1])):
        # select if population count and area size is almost the same
        if poly_layer['pop'][poly_idx] == poly_layer['pop'][poly_idx + 1] and \
                round(poly_layer['area'][poly_idx], 7) == round(poly_layer['area'][poly_idx + 1], 7):
            poly_list.append(poly_layer['counter'][poly_idx])

    # drop rows from df
    df = poly_layer[~poly_layer['counter'].isin(poly_list)]

    result_geodf = gpd.GeoDataFrame(df, geometry='geometry')

    return result_geodf


def calculate_fragment_values(pop_raster, poly_layer=None, add_columns=False):
    """Calculates population sum per isochrone."""
    pop_data = []

    for poly_idx, poly_cap, poly_geom in zip(poly_layer['counter'], poly_layer['cap_int'], poly_layer['geometry']):
        feature = gpd.GeoSeries([poly_geom]).to_json()
        pop_stats = zonal_stats(feature, pop_raster, stats=['sum'])  # calculate population for given area
        poly_area = area(mapping(poly_geom)) / 1e+6  # in kilometer
        pop_data.append([poly_idx, poly_cap, pop_stats[0]['sum'], poly_area, poly_geom])

    df = pd.DataFrame(pop_data, columns=['counter', 'cap_int', 'pop', 'area', 'geometry'])
    df['pop'].fillna(0, inplace=True)

    if add_columns is True:
        df['cap_pop'] = (df['cap_int']/df['pop']) * 100000
        df['pop_area'] = df['pop']/df['area']  # population density
        df['cap_dens'] = df['cap_int'] / df['pop_area']

    df = df.replace([np.inf, -np.inf], np.nan)
    result_geodf = gpd.GeoDataFrame(df, geometry='geometry')

    return result_geodf


def normal_flooded_union(normal_layer, scenario_layer):
    """Applies union to receive all possible geometries"""

    # drop entries with missing and empty geometries and spply buffer around each geometry
    normal_cleaned = normal_layer[~(normal_layer['geometry'].is_empty | normal_layer['geometry'].isna())]
    normal_cleaned = normal_cleaned[['counter', 'cap_int', 'geometry']]
    normal_cleaned.geometry = normal_cleaned.geometry.buffer(0.000001).copy()

    # drop entries with missing and empty geometries
    scenario_cleaned = scenario_layer[~(scenario_layer['geometry'].is_empty | scenario_layer['geometry'].isna())]
    normal_cleaned = normal_cleaned[['counter', 'cap_int', 'geometry']]
    normal_cleaned.geometry = normal_cleaned.geometry.buffer(0.000001).copy()

    # apply union overlay
    result_geodf = gpd.overlay(normal_cleaned, scenario_cleaned, how='union')

    return result_geodf


def calculate_column_change(pop_raster, poly_layer):
    """Calculates flood impact per isochrone for each column."""
    pop_data = []
    poly_layer = poly_layer[['counter_1', 'cap_int_1', 'counter_2', 'cap_int_2', 'geometry']]

    for poly_idx_n, poly_cap_n, poly_idx_2, poly_cap_2, poly_geom in zip(poly_layer['counter_1'],
                                                                         poly_layer['cap_int_1'],
                                                                         poly_layer['counter_2'],
                                                                         poly_layer['cap_int_2'],
                                                                         poly_layer['geometry']):
        feature = gpd.GeoSeries([poly_geom]).to_json()
        # drop geometries with an area size smaller than 1m²
        if area(mapping(poly_geom)) > 0.000009039:
            # calculate population for given area
            pop_stats = zonal_stats(feature, pop_raster, stats=['sum'])
            poly_area = area(mapping(poly_geom)) / 1e+6  # in kilometer
            pop_data.append([poly_idx_n, poly_cap_n, poly_idx_2, poly_cap_2, pop_stats[0]['sum'], poly_area, poly_geom])

    df = pd.DataFrame(pop_data, columns=['counter_1', 'cap_int_1', 'counter_2', 'cap_int_2', 'pop', 'area', 'geometry'])
    df.dropna(subset=['pop'])

    df['pop_area'] = df['pop'] / df['area']  # population density
    df['cap_pop'] = (df['cap_int_1'] / df['pop']) * 100000
    df['cap_dens'] = df['cap_int_1'] / df['pop_area']
    df['cap_dens_2'] = df['cap_int_2'] / df['pop_area']
    df['cap_dens_d'] = df['cap_dens_2'] - df['cap_dens']

    df = df.replace([np.inf, -np.inf], np.nan)
    result_geodf = gpd.GeoDataFrame(df, geometry='geometry')

    return result_geodf


def stats(access_result_geodf, column_name, percentile_value):
    """Calculates percentile value; Useful for data interpretation and visualisation """
    df_np = access_result_geodf[column_name].to_numpy()

    print(str(percentile_value), ' percentile:', np.nanpercentile(df_np, int(percentile_value)))
    print('Std.:', np.std(df_np))
    print('Std., ignoring NaNs:', np.nanstd(df_np))
    print('Variance, ignoring NaNs:', np.nanvar(df_np))
    print('Mean:', np.mean(df_np))
    print('Mean, ignoring NaNs:', np.nanmean(df_np))


if __name__ == '__main__':

    scenario_name = None
    analysis_part = None
    amenity_type_input = 'hospital'
    time_range = 300  # 5 minutes
    pop_layer = path.join(DATA_DIR, SETTINGS['population']['extract'])
    iso_boundaries_layer = None
    column_name_input = None
    percentile_value_input = None

    try:
        analysis_part = str(sys.argv[1])
    except KeyError:
        logging.error('')

    if analysis_part == 'analysis':

        try:
            scenario_name = str(sys.argv[2])
        except KeyError:
            logging.error('Please provide one scenario name, e.g., normal or flooded.')

        try:
            amenity_type_input = str(sys.argv[3])
            time_range = int(sys.argv[4])
        except IndexError:
            pass

        if not path.exists(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'])):
            mkdir(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results']))
            print('Directory', path.join(DATA_DIR, SETTINGS['supply_demand']['path_results']), 'created.')

        # add health data to isochrones
        iso_cap_layer = add_capacity_data(scenario_name, amenity_type_input, time_range)
        # create overlay layer
        iso_boundaries_layer = create_boundaries(iso_cap_layer)
        # calculate values of overlapping areas
        cum_overlap_layer = intersect_overlap(scenario_name, iso_cap_layer, iso_boundaries_layer)

        # add additional information like population amount
        area_lyr = calculate_fragment_values(pop_layer, cum_overlap_layer, False)
        cleaned_lyr = drop_similar_entries(area_lyr)
        supply_demand_geodf = calculate_fragment_values(pop_layer, cleaned_lyr, True)

        # save data
        supply_demand_geodf.to_file(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'],
                                              SETTINGS['supply_demand'][scenario_name]), driver='ESRI Shapefile')
        print(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'], SETTINGS['supply_demand'][scenario_name]),
              'saved')

        if scenario_name == 'flooded':

            supply_demand_normal = gpd.read_file(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'],
                                                           SETTINGS['supply_demand']['normal']))
            city_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))

            # calculate flood impact
            union_result = normal_flooded_union(supply_demand_normal, supply_demand_geodf)
            impact_result = calculate_column_change(pop_layer, union_result)
            # calculate city difference to receive only data within the city
            impact_result_city = admin_border.border_intersect(city_layer, impact_result)

            # save impact data
            impact_result_city.to_file(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'],
                                            SETTINGS['supply_demand']['impact']), driver='ESRI Shapefile')
            print(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'], SETTINGS['supply_demand']['impact']),
                  'saved')

    elif analysis_part == 'stats':

        try:
            column_name_input = str(sys.argv[2])
        except IndexError:
            logging.error('Please provide a valid column name of the processed file:',
                          path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'],
                                    SETTINGS['supply_demand']['flooded']))

        try:
            percentile_value_input = sys.argv[3]
        except IndexError:
            logging.error('Please provide a percentile between 0 and 100.')

        # load processed impact file
        impact_geodf = gpd.read_file(path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'],
                                               SETTINGS['supply_demand']['flooded']), driver='ESRI Shapefile')

        # check if column exists in input file
        if column_name_input not in impact_geodf:
            print('Please provide a valid column name of the processed file:',
                  path.join(DATA_DIR, SETTINGS['supply_demand']['path_results'],
                            SETTINGS['supply_demand']['flooded']))
            sys.exit()

        # run percentile function
        stats(impact_geodf, column_name_input, percentile_value_input)
