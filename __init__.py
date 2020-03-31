# -*- coding: utf-8 -*-
from os import path
import geopandas as gpd
import fiona as fn
import rasterio

BASEDIR = path.join(path.abspath(path.dirname(__file__)))

# input
jakarta_border = gpd.read_file(path.join(BASEDIR, 'ma_jakarta/data/input/jakarta_border.geojson'))
jakarta_border_fn = fn.open(path.join(BASEDIR, 'ma_jakarta/data/input/jakarta_border.geojson'))

flooded_shp = gpd.read_file('/home/isabell/Workspace/test/ma/ma-jakarta/data/flood_data/flooded_yes/flooded_layer.shp')
floodprone_input = fn.open(path.join(BASEDIR, 'ma_jakarta/data/input/RW-DKI-Jakarta.gpkg'))

amenity_data = gpd.read_file('/home/isabell/Workspace/test/ma/ma-jakarta/data/amenity/amenity.geojson')
amenity_data_fn = fn.open('/home/isabell/Workspace/test/ma/ma-jakarta/data/amenity/amenity.geojson')

pop_raster = rasterio.open('/home/isabell/Workspace/test/ma/ma-jakarta/data/idn_ppp_2020.tif')

# output
floodprone_shp = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/floodprone.shp')

amenities_all = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/amenities_all.shp')
amenities_prone = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/amenities_prone.shp')
amenities_flooded = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/amenities_flooded.shp')

pop_raster_extract = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/idn_ppp_2020_extract.tif')


# network
network_path = path.join(BASEDIR, 'ma_jakarta/network_graphs')
network_prone = path.join(BASEDIR, 'ma_jakarta/network_graphs/floodprone')
network_flooded = path.join(BASEDIR, 'ma_jakarta/network_graphs/flooded')


# ors
api_key = 'your-api-key'
iso_normal = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/iso_normal.shp')
iso_prone = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/iso_prone.shp')
iso_flooded = path.join(BASEDIR, 'ma_jakarta/data/preprocessed/iso_flooded.shp')
