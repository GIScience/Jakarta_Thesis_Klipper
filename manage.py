# -*- coding: utf-8 -*-
from __init__ import flooded_shp, floodprone_input, floodprone_shp, \
    amenity_data, jakarta_border, jakarta_border_fn, \
    amenity_data_fn, amenities_all, amenities_prone, amenities_flooded, \
    pop_raster, pop_raster_extract, \
    network_path, network_flooded, network_prone, \
    api_key, iso_normal, iso_prone, iso_flooded

from ma_jakarta.scripts.data_preprocessing import flooprone, amenities, population
from ma_jakarta.scripts.network import network_preparation
from ma_jakarta.scripts.ors import graph_preparation, isochrone

from os import path
import geopandas as gpd
import logging

# preprocessing
if not path.isfile(floodprone_shp):
    flooprone.floodprone_selection(floodprone_input, floodprone_shp)
    logging.info('Floodprone related objects saved:', floodprone_shp)
else:
    logging.info(floodprone_shp, 'already exists.')
    floodprone_shp = gpd.read_file(floodprone_shp)

# call amenity class
amenity_prep = amenities.Amenities(amenity_data_fn, jakarta_border, floodprone_shp)

if not path.isfile(amenities_all):
    amenities_preprocessed = amenity_prep.preprocessing(amenities_all)
else:
    logging.info(amenities_all, 'already exists.')

if not path.isfile(amenities_prone):
    amenity_prep.select_amenities(amenities_preprocessed, floodprone_shp, amenities_prone)
else:
    logging.info(amenities_prone, 'already exists.')

if not path.isfile(amenities_flooded):
    amenity_prep.select_amenities(amenities_preprocessed, flooded_shp, amenities_flooded)
else:
    logging.info(amenities_flooded, 'already exists.')


if not path.isfile(pop_raster_extract):
    population.extract_raster_part(pop_raster, jakarta_border_fn, pop_raster_extract)
else:
    logging.info(pop_raster_extract, 'already exists.')


# network
network_graph = network_preparation.download_network('Jakarta, Indonesia', 'drive', 'normal', network_path)
network_preparation.flood_intersection(network_graph, floodprone_shp, network_prone)
network_preparation.flood_intersection(network_graph, flooded_shp, network_flooded)

# ors
file_converter = graph_preparation.ORSGraphPrep(network_prone, 'floodprone').convert()

# adjust docker-compose.yml: OSM_FILE and volumes
# make sure there is no docker/graph folder existing.
# If, rename to e.g. graphs_floodprone to keep data. ORS builds graph from "graphs" folder
# in folder openrouteservice/docker: docker-compose up -d

logging.info('Make sure to first build correct ORS graph! E.g. floodprone graph for floodprone isochrone request.')
isochrone.iso_request(api_key, amenities_all, iso_normal)
# isochrone.iso_request(api_key, amenities_prone, iso_prone)
# isochrone.iso_request(api_key, amenities_flooded, iso_flooded)
