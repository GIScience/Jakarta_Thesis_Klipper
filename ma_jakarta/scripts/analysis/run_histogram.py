# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from ma_jakarta.scripts.analysis import reached_values, histogram
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from os import path

# TODO: combine into one dict and loop for create_histogram
union_area_dict = {}
union_pop_dict = {}
union_node_dict = []
union_btwn_dict = []
union_cls_dict = []

for iso_scenario in SETTINGS['reached']:
    scenario_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['reached'][iso_scenario]))
    modified_layer = reached_values.dissolve_layer(scenario_layer)

    if iso_scenario != 'normal':
        modified_layer = reached_values.flood_difference(modified_layer, iso_scenario)

    union_area_dict[iso_scenario] = {}
    union_area = reached_values.reached_area(modified_layer)
    union_area_dict[iso_scenario].update(union_area)

    union_pop_dict[iso_scenario] = {}
    union_pop = reached_values.reached_pop(modified_layer)
    union_pop_dict[iso_scenario].update(union_pop)

    # union_node_dict[iso_scenario] = {}
    # union_btwn_dict[iso_scenario] = {}
    # union_cls_dict[iso_scenario] = {}
    union_node, union_btwn, union_cls = reached_values.reached_nodes_sjoin(modified_layer, iso_scenario)
    union_node_dict.append(union_node)
    union_btwn_dict.append(union_btwn)
    union_cls_dict.append(union_cls)
    # union_node_dict[iso_scenario].update(union_node)
    # union_btwn_dict[iso_scenario].update(union_btwn)
    # union_cls_dict[iso_scenario].update(union_cls)

node_merged = pd.concat([layer for layer in union_node_dict])
node_merged.to_csv(path.join(DATA_DIR, 'results/tables/reached_nodes_union.csv'))
btwn_merged = pd.concat([layer for layer in union_btwn_dict])
btwn_merged.to_csv(path.join(DATA_DIR, 'results/tables/reached_btwn_union.csv'))
cls_merged = pd.concat([layer for layer in union_cls_dict])
cls_merged.to_csv(path.join(DATA_DIR, 'results/tables/reached_cls_union.csv'))

histogram.create_table(node_merged, path.join(DATA_DIR, 'results/tables/reached_nodes_union.png'))
histogram.create_table(btwn_merged, path.join(DATA_DIR, 'results/tables/reached_btwn_union.png'))
cls_plt = histogram.create_table(cls_merged, path.join(DATA_DIR, 'results/tables/reached_cls_union.png'))
print('d')

# TODO: amount of subgraphs
# fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(18, 10))
# for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
#     histogram.create_histogram(union_area_dict, amenity, ax, 'Reached Area [km2]', 'area', 1e-6)

# plt.tight_layout()
# plt.savefig(path.join(DATA_DIR, 'results/plots/reached_area_union2.png'))


# TODO: amount of subgraphs
# fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(18, 10))
# for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
#     histogram.create_histogram(union_pop_dict, amenity, ax, 'Reached Population [mil]', 'population', 1e-6)

# plt.tight_layout()
# plt.savefig(path.join(DATA_DIR, 'results/plots/reached_pop_union.png'))

# TODO: amount of subgraphs
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(18, 10))
for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
    histogram.create_histogram(union_node_dict, amenity, ax, 'Reached nodes', 'Reached nodes', 1)
plt.tight_layout()
plt.savefig(path.join(DATA_DIR, 'results/tables/reached_nodes_union.png'))

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(18, 10))
for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
    histogram.create_histogram(union_btwn_dict, amenity, ax, 'Betweenness Centrality [normalized]',
                               'Mean Betweenness Centrality', 1e+6)
plt.tight_layout()
plt.savefig(path.join(DATA_DIR, 'results/tables/reached_btwn_union.png'))

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(18, 10))
for amenity, ax in zip(SETTINGS['amenity_osm_values'], axes.flatten()):
    histogram.create_histogram(union_cls_dict, amenity, ax, 'Closeness Centrality [normalized]',
                               'Mean Closeness Centrality', 1e+3)
plt.tight_layout()
plt.savefig(path.join(DATA_DIR, 'results/tables/reached_cls_union.png'))
