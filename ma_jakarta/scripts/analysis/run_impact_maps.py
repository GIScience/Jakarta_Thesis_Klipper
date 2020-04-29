# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from ma_jakarta.scripts.analysis import reached_values
from ma_jakarta.scripts.analysis import impact_maps
import geopandas as gpd
import pandas as pd
from os import path

# TODO: combine with tun_histogram to keep preprocessed files?
normal_punched = None
flood_punched = []
for iso_scenario in SETTINGS['reached_2']:
    if iso_scenario == 'normal':
        normal_scenario = gpd.read_file(path.join(DATA_DIR, SETTINGS['reached_2'][iso_scenario]))
        normal_union = reached_values.dissolve_layer(normal_scenario)
        normal_punched = impact_maps.punch_layer(normal_union, iso_scenario)
    else:
        scenario_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['reached_2'][iso_scenario]))
        union_layer = reached_values.dissolve_layer(scenario_layer)
        intersected_layer = reached_values.flood_difference(union_layer, iso_scenario)
        punched_layer = impact_maps.punch_layer(intersected_layer, iso_scenario)
        flood_punched.append(punched_layer)

flood_merged = pd.concat([layer for layer in flood_punched])

if normal_punched is not None and len(flood_punched) != 0:
    for iso_scenario in SETTINGS['reached_2']:
        if iso_scenario != 'normal':
            flood_geodf = flood_merged.loc[flood_merged['scenario'] == iso_scenario]
            impact_maps.union_access(normal_punched, flood_geodf, iso_scenario)
