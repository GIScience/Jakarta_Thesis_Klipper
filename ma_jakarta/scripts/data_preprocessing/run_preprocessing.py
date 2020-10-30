# -*- coding: utf-8 -*-
from __init__ import SETTINGS, DATA_DIR
from ma_jakarta.scripts.data_preprocessing import admin_border, floods, amenities, hot_amenities, population
from os import path, mkdir, listdir
import geopandas as gpd
import pandas as pd
import fiona as fn
import rasterio
import sys
import logging


if __name__ == '__main__':

    hot_data = None
    try:
        hot_data = sys.argv[1]
    except IndexError:
        pass

    if not path.exists(path.join(DATA_DIR, 'preprocessed')):
        mkdir(path.join(DATA_DIR, 'preprocessed'))

    try:
        # city border
        city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['input']))

        if city_border.geometry.count() == 1:
            city_border.to_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']), driver='ESRI Shapefile')

        elif city_border.geometry.count() > 1:
            border_union = admin_border.border_union(city_border)
            border_union.to_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']), driver='ESRI Shapefile')

        print(SETTINGS['city_border']['preprocessed'], 'saved.')

    except Exception as err:
        logging.error(err)

    try:
        # flood
        city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))
        flood_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['input']))

        flood_union = floods.flood_union(flood_data)
        flood_union.to_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed']), driver='ESRI Shapefile')
        print(SETTINGS['flood']['preprocessed'], 'saved.')

    except Exception as err:
        logging.error(err)

    try:
        # amenities
        city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))
        flood_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed']))

        if hot_data is not None:
            hot_files = []
            hot_data_path = path.join(DATA_DIR, SETTINGS['amenities']['data_hot'])

            # select shapefiles
            file_names = [pos_json for pos_json in listdir(hot_data_path) if pos_json.endswith('.shp')]
            for index, shp_file in enumerate(file_names):
                with fn.open(path.join(hot_data_path, shp_file), 'r') as hot_file:
                    amenity_prep = amenities.Amenities(hot_file, city_border)
                    city_amenities_single_file = amenity_prep.preprocessing()
                    hot_files.append(city_amenities_single_file)

            # concat to one dataframe
            hot_amenities_all = pd.concat([layer for layer in hot_files])

            # adjust HOT related capacity values
            hot_amenity_prep = hot_amenities.HotAmenities(hot_amenities_all)
            city_amenities = hot_amenity_prep.run_capacity()

        else:
            amenity_data_fn = fn.open(path.join(DATA_DIR, SETTINGS['amenities']['data']))

            # load class and functions
            amenity_prep = amenities.Amenities(amenity_data_fn, city_border)
            city_amenities = amenity_prep.preprocessing()

        # output path normal scenario data
        amenities_all = path.join(DATA_DIR, SETTINGS['amenities']['normal'])
        city_amenities.to_file(amenities_all, driver='ESRI Shapefile')
        print(SETTINGS['amenities']['normal'], 'saved.')

        # output path for flooded scenario
        amenities_flooded = path.join(DATA_DIR, SETTINGS['amenities']['flooded'])
        selected_amenities = amenity_prep.select_amenities(city_amenities, flood_data)
        selected_amenities.to_file(amenities_flooded, driver='ESRI Shapefile')
        print(SETTINGS['amenities']['flooded'], 'saved.')

    except Exception as err:
        logging.error(err)

    try:
        # population
        pop_raster = rasterio.open(path.join(DATA_DIR, SETTINGS['population']['data']))
        city_border_fn = fn.open(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))
        # output path
        pop_raster_extract = path.join(DATA_DIR, SETTINGS['population']['extract'])

        population.extract_raster_part(pop_raster, city_border_fn, pop_raster_extract)
        print(SETTINGS['population']['data'], 'saved.')

    except Exception as err:
        logging.error(err)
