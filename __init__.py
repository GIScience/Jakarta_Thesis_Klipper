# -*- coding: utf-8 -*-
from os import path
from yaml import safe_load

BASEDIR = path.abspath(path.dirname(__file__))
DATA_DIR = path.join(BASEDIR, 'ma_jakarta/data')
NETWORK_DIR = path.join(BASEDIR, 'ma_jakarta/network_graphs')

SETTINGS = safe_load(open(path.join(BASEDIR, 'ma_jakarta/settings.yml')))
