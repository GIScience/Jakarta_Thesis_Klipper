# -*- coding: utf-8 -*-
from shapely.geometry import shape
from shapely import ops
import pandas as pd
import geopandas as gpd


def flood_union(flood_layer):
    """Dissolve flood layer"""
    # create buffer around geometries to remove small fractions
    flood_layer.geometry = flood_layer.geometry.buffer(0.000001).copy()

    flood_geom = []
    for poly in range(len(flood_layer)):
        if flood_layer['geometry'][poly] is not None:
            flood_geom.append(shape(flood_layer['geometry'][poly]))

    flood_boundary = ops.cascaded_union(flood_geom)

    df = pd.DataFrame(flood_boundary, columns=['geometry'])
    geodf = gpd.GeoDataFrame(df, geometry='geometry')

    return geodf


def flood_difference(input_layer, flood_layer):
    """
    Calculate difference of given input layer (e.g. city border or isochrones) and flood scenario.
    https://geopandas.org/set_operations.html
    """
    layer_difference = gpd.overlay(input_layer, flood_layer, how='difference')

    return layer_difference
