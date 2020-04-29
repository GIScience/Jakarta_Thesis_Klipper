# -*- coding: utf-8 -*-
from __init__ import SETTINGS, BASEDIR, DATA_DIR
from ma_jakarta.scripts.data_preprocessing import flooprone, amenities, population
from os import path
import geopandas as gpd
import logging
import fiona as fn
import rasterio

try:
    # TODO: adjust paths in SETTINGS.yml
    # floodprone data
    floodprone_input = fn.open(path.join(DATA_DIR, SETTINGS['floodprone_input']))
    floodprone_shp = path.join(DATA_DIR, SETTINGS['floodprone'])
    # run floodprone preprocessing
    flooprone.floodprone_selection(floodprone_input, floodprone_shp)
    print('Floodprone related objects saved:', floodprone_shp)

    # amenity data
    # amenity_data_fn = fn.open(SETTINGS['amenity_data'])
    amenity_data_fn = fn.open(path.join(DATA_DIR, SETTINGS['amenity_data']))
    jakarta_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['jakarta_border']))
    flooded_shp = gpd.read_file(path.join(DATA_DIR, SETTINGS['flooded']))
    floodprone_shp = gpd.read_file(floodprone_shp)

    amenities_all = path.join(DATA_DIR, SETTINGS['amenities_all'])
    amenities_prone = path.join(DATA_DIR, SETTINGS['amenities_prone'])
    amenities_flooded = path.join(DATA_DIR, SETTINGS['amenities_flooded'])

    # run amenity preprocessing
    amenity_prep = amenities.Amenities(amenity_data_fn, jakarta_border, floodprone_shp)
    amenities_preprocessed = amenity_prep.preprocessing(amenities_all)
    amenity_prep.select_amenities(amenities_preprocessed, floodprone_shp, amenities_prone)
    amenity_prep.select_amenities(amenities_preprocessed, flooded_shp, amenities_flooded)

    # population
    # pop_raster = rasterio.open(SETTINGS['pop_raster'])
    pop_raster = rasterio.open(path.join(DATA_DIR, SETTINGS['pop_raster']))
    jakarta_border_fn = fn.open(path.join(BASEDIR, SETTINGS['jakarta_border']))
    pop_raster_extract = path.join(DATA_DIR, SETTINGS['pop_raster_extract'])

    population.extract_raster_part(pop_raster, jakarta_border_fn, pop_raster_extract)
    print('Population extract saved:', pop_raster_extract)

    print('Preprocessing done successfully.')

except Exception as err:
    print(err)
