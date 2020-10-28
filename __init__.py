# -*- coding: utf-8 -*-
from os import path
from yaml import safe_load
import geopandas as gpd

BASEDIR = path.abspath(path.dirname(__file__))
DATA_DIR = path.join(BASEDIR, 'ma_jakarta/data')
NETWORK_DIR = path.join(BASEDIR, 'ma_jakarta/network_graphs')

SETTINGS = safe_load(open(path.join(BASEDIR, 'ma_jakarta/settings.yml')))

border_crs = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['input'])).crs
