# -*- coding: utf-8 -*-
from __init__ import border_crs
from shapely import ops
import pandas as pd
import geopandas as gpd


def border_union(city_layer):
    """Dissolve flood layer"""
    city_boundary = ops.cascaded_union(city_layer['geometry'])

    df = pd.DataFrame(city_boundary, columns=['geometry'])
    geodf = gpd.GeoDataFrame(df, geometry='geometry')

    return geodf


def border_intersect(border_layer, iso_layer):
    """Intersect data layer, e.g. isochrone layer, with city border to receive only results within city.
    https://geopandas.org/set_operations.html"""
    iso_layer = gpd.GeoDataFrame(iso_layer, geometry='geometry')
    iso_layer.crs = border_crs
    
    intersected_layer = gpd.overlay(iso_layer, border_layer, how='intersection')

    return intersected_layer
