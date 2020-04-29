# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, NETWORK_DIR, SETTINGS
from shapely.geometry import mapping, shape
from shapely import ops
import pandas as pd
import geopandas as gpd
from os import path
from area import area
from rasterstats import zonal_stats


def dissolve_layer(iso_layer):
    """Dissolves the isochrone layer first by amenity type and second by range value to determine the reached values."""
    amenities = SETTINGS['amenity_osm_values']
    dis_layer = []

    for amenity in amenities:
        iso_amenities = iso_layer[iso_layer['amenity'] == amenity]
        iso_dissolved = iso_amenities.dissolve(by='value', as_index=False)
        dis_layer.append(iso_dissolved)

    result_merged = pd.concat([layer for layer in dis_layer])

    return result_merged


def flood_layer_union(flood_layer):
    # TODO: rewrite docstring -> fix..
    """Fix geometry to calculate difference overlay with border layer. Needed to select flooded amenities"""
    flood_geom = []

    for poly in range(len(flood_layer)):
        if flood_layer['geometry'][poly] is not None:
            flood_geom.append(shape(flood_layer['geometry'][poly]))
    union_l = ops.cascaded_union(flood_geom)

    df = pd.DataFrame(union_l, columns=['geometry'])
    geodf = gpd.GeoDataFrame(df, geometry='geometry')

    return geodf


def flood_difference(iso_dissolved, scenario):
    flood_data = gpd.read_file(path.join(DATA_DIR, SETTINGS[scenario]))
    flood_union = flood_layer_union(flood_data)

    iso_intersected = gpd.overlay(iso_dissolved, flood_union, how='difference')

    return iso_intersected


def reached_area(iso_layer):
    """Calculate reached area"""
    amenities = SETTINGS['amenity_osm_values']
    area_data = {}

    for amenity in amenities:
        area_data[amenity] = {}

    for amenity, iso_value, iso_geom in zip(iso_layer['amenity'], iso_layer['value'], iso_layer['geometry']):
        area_size = area(mapping(iso_geom))
        area_data[amenity][iso_value] = area_size

    return area_data


def reached_pop(iso_layer):
    """Calculate population sum per isochrone."""
    pop_raster = path.join(DATA_DIR, SETTINGS['pop_raster_extract'])
    amenities = SETTINGS['amenity_osm_values']
    range_values = SETTINGS['iso_range_values']
    pop_data = {}

    for amenity in amenities:
        pop_data[amenity] = {}

    for iso_amenity, iso_value, iso_geom in zip(iso_layer['amenity'], iso_layer['value'], iso_layer['geometry']):
        for amenity in amenities:
            for range_value in range_values:
                if iso_amenity == amenity and iso_value == range_value:
                    feature = gpd.GeoSeries([iso_geom]).to_json()
                    stats = zonal_stats(feature, pop_raster, stats=['sum'])
                    pop_data[amenity][range_value] = stats[0]['sum']

    return pop_data


def reached_nodes_sjoin(iso_layer, scenario):
    """Caluclate reached nodes and mean centrality per isochrone."""
    gdf_iso = gpd.GeoDataFrame(iso_layer, geometry='geometry')
    gdf_nodes = gpd.read_file(path.join(NETWORK_DIR, SETTINGS['networks'][scenario]))

    # spatial join of normal and flood layer
    gdf_joined = gpd.sjoin(gdf_nodes, gdf_iso, how="left", op='within')

    # calculate reached nodes, mean betweenness and mean closeness centrality
    nodes_amount = pd.DataFrame({'amount': gdf_joined.groupby(['amenity', 'value']).size()}).reset_index()
    btwn_mean = gdf_joined.groupby(['amenity', 'value'], as_index=False)['btwn'].mean()
    cls_mean = gdf_joined.groupby(['amenity', 'value'], as_index=False)['cls'].mean()

    nodes_amount['scenario'] = scenario
    btwn_mean['scenario'] = scenario
    cls_mean['scenario'] = scenario

    return nodes_amount, btwn_mean, cls_mean
