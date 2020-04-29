# -*- coding: utf-8 -*-
from __init__ import SETTINGS, DATA_DIR
from ma_jakarta.scripts.data_preprocessing import floods, amenities, population
from os import path, mkdir
import geopandas as gpd
import fiona as fn
import rasterio

if not path.exists(path.join(DATA_DIR, 'preprocessed')):
    mkdir(path.join(DATA_DIR, 'preprocessed'))

# try:
#     # floodprone data
#     floodprone_input = fn.open(path.join(DATA_DIR, SETTINGS['floodprone_input']))
#     floodprone_shp = path.join(DATA_DIR, SETTINGS['floodprone'])
#     # run floodprone preprocessing
#     flooprone.floodprone_selection(floodprone_input, floodprone_shp)
#     print('Floodprone related objects saved:', floodprone_shp)
# except Exception as err:
#     print(err)

try:
    city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']))

    for flood_layer in SETTINGS['flood']['input']:
        flood_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['input'][flood_layer]))
        flood_union = floods.flood_union(flood_data)
        flood_intersection = floods.flood_intersection(city_border, flood_union)
        flood_intersection.to_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed'][flood_layer]), driver='ESRI Shapefile')

except Exception as err:
    print(err)

try:
    # amenities
    amenity_data_fn = fn.open(path.join(DATA_DIR, SETTINGS['amenities']['data']))
    city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']))

    amenities_all = path.join(DATA_DIR, SETTINGS['amenities']['normal'])
    amenity_prep = amenities.Amenities(amenity_data_fn, city_border)
    amenities_preprocessed = amenity_prep.preprocessing(amenities_all)

    for flood_layer in SETTINGS['flood']['preprocessed']:
        flood_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed'][flood_layer]))
        amenities_flooded = path.join(DATA_DIR, SETTINGS['amenities'][flood_layer])
        amenity_prep.select_amenities(amenities_preprocessed, flood_data, amenities_flooded)

except Exception as err:
    print(err)

try:
    # population
    pop_raster = rasterio.open(path.join(DATA_DIR, SETTINGS['population']['data']))
    city_border_fn = fn.open(path.join(DATA_DIR, SETTINGS['city_border']))
    pop_raster_extract = path.join(DATA_DIR, SETTINGS['population']['extract'])

    population.extract_raster_part(pop_raster, city_border_fn, pop_raster_extract)
    print('Population extract saved:', pop_raster_extract)

except Exception as err:
    print(err)

print('Preprocessing done.')

