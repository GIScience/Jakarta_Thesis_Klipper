# -*- coding: utf-8 -*-
from __init__ import SETTINGS
from shapely.geometry import mapping
import pandas as pd
import geopandas as gpd
from area import area
from rasterstats import zonal_stats


def dissolve_layer(iso_layer):
    """Dissolves the isochrone layer first by amenity type and second by range value to determine the reached values."""
    amenities = SETTINGS['amenity_osm_values']
    dis_layer = []

    for amenity in amenities:
        iso_amenities = iso_layer[iso_layer['amenity'] == amenity].copy()
        iso_dissolved = iso_amenities.dissolve(by='value', as_index=False)
        dis_layer.append(iso_dissolved)

    result_merged = pd.concat([layer for layer in dis_layer])

    return result_merged


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


def total_city_area(city_layer):
    """Calculate total city area size"""
    city_area = area(city_layer[0]['geometry'])

    return city_area


def reached_pop(pop_raster, iso_layer):
    """Calculate population sum per isochrone."""
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


def total_city_pop(pop_raster, city_layer):
    """Calculate amount of total city population"""
    stats = zonal_stats(city_layer[0]['geometry'], pop_raster, stats=['sum'])

    return stats[0]['sum']
