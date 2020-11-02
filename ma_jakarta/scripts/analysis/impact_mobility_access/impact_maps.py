# -*- coding: utf-8 -*-
from __init__ import SETTINGS, border_crs
from ma_jakarta.scripts.data_preprocessing import floods
import pandas as pd
import geopandas as gpd


def punch_layer(iso_df, scenario):
    """Calculate layer difference."""
    amenities = SETTINGS['amenity_osm_values']
    punched_dir = []

    for amenity in amenities:
        dif_object = []
        amenity_df = iso_df.loc[iso_df['amenity'] == amenity]
        for i in range(len(amenity_df)):
            if i == 0:  # value = 300
                dif_object.append([amenity_df.loc[i]['value'], amenity_df.loc[i]['geometry'],
                                   amenity_df.loc[i]['amenity_id'],
                                   amenity_df.loc[i]['iso_id'], amenity_df.loc[i]['amenity']])
            else:
                if amenity_df.loc[i]['geometry'].difference(amenity_df.loc[i - 1]['geometry']).is_empty:
                    dif_geom = None
                else:
                    dif_geom = amenity_df.loc[i]['geometry'].difference(amenity_df.loc[i - 1]['geometry'])
                dif_object.append([amenity_df.loc[i]['value'], dif_geom, amenity_df.loc[i]['amenity_id'],
                                   amenity_df.loc[i]['iso_id'], amenity_df.loc[i]['amenity']])

        amenity_df_modi = pd.DataFrame(dif_object, columns=['value', 'geometry', 'amenity_id', 'iso_id', 'amenity'])
        amenity_geodf = gpd.GeoDataFrame(amenity_df_modi, geometry='geometry')
        punched_dir.append(amenity_geodf)

    punched_result = pd.concat([layer for layer in punched_dir])
    punched_result['scenario'] = scenario

    return punched_result


def union_access(access_layer1, access_layer2, amenity, city_border, flood_layer):
    """Union overlay of complete and flood layer to calculate the range value change of health sites isochrones."""
    res_union = None

    amenity_df1 = access_layer1.loc[access_layer1.amenity == amenity].copy()
    amenity_df1 = amenity_df1.dropna(subset=['geometry'])
    amenity_df2 = access_layer2.loc[access_layer2.amenity == amenity].copy()
    amenity_df2 = amenity_df2.dropna(subset=['geometry'])

    # small buffer around each isochrone to keep correct geometry
    amenity_df1.geometry = amenity_df1.geometry.buffer(0.000001).copy()
    amenity_df2.geometry = amenity_df2.geometry.buffer(0.000001).copy()
    gdf1 = gpd.GeoDataFrame(amenity_df1, geometry='geometry')
    gdf2 = gpd.GeoDataFrame(amenity_df2, geometry='geometry')
    # set the same crs as the city border holds
    gdf1.crs = border_crs
    gdf2.crs = border_crs
    # intersect data with city border to receive only results within city
    gdf1_intersected = gpd.overlay(gdf1, city_border, how='intersection')
    gdf2_intersected = gpd.overlay(gdf2, city_border, how='intersection')

    # if the complete area can be already reached with the not highest isochrone range value
    try:
        res_union = gpd.overlay(gdf1_intersected, gdf2_intersected, how='union')
    except AttributeError:
        pass

    # value means range value
    res_union['dif'] = res_union['value_2'] - res_union['value_1']

    # Calculates difference of isochrones and flood areas.
    # Needed due to wrongly created areas due to simplification in isochrone algorithm
    modified_layer = floods.flood_difference(res_union, flood_layer)

    return modified_layer
