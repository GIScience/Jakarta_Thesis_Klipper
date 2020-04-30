# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
import pandas as pd
import geopandas as gpd
from os import path


def punch_layer(iso_df, scenario):
    """Calcuclate layer difference."""
    amenities = SETTINGS['amenity_osm_values']
    punched_dir = []

    for amenity in amenities:
        dif_object = []
        amenity_df = iso_df.loc[iso_df['amenity'] == amenity]
        for i in range(len(amenity_df)):
            if i == 0:  # value = 300
                dif_object.append([amenity_df.loc[i]['value'], amenity_df.loc[i]['geometry'], amenity_df.loc[i]['id'],
                                   amenity_df.loc[i]['iso_id'], amenity_df.loc[i]['amenity']])
            else:
                if amenity_df.loc[i]['geometry'].difference(amenity_df.loc[i - 1]['geometry']).is_empty:
                    dif_geom = None
                else:
                    dif_geom = amenity_df.loc[i]['geometry'].difference(amenity_df.loc[i - 1]['geometry'])
                dif_object.append([amenity_df.loc[i]['value'], dif_geom,
                                   amenity_df.loc[i]['id'], amenity_df.loc[i]['iso_id'], amenity_df.loc[i]['amenity']])

        amenity_df_modi = pd.DataFrame(dif_object, columns=['value', 'geometry', 'id', 'iso_id', 'amenity'])
        amenity_geodf = gpd.GeoDataFrame(amenity_df_modi, geometry='geometry')
        punched_dir.append(amenity_geodf)

    punched_result = pd.concat([layer for layer in punched_dir])
    punched_result['scenario'] = scenario

    return punched_result


def union_access(access_layer1, access_layer2, scenario):
    """Union overlay of complete and flood layer to calculate the range value change of healthsites isochrones."""
    res_union = None
    city_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']))
    city_crs = city_border.crs

    for amenity in SETTINGS['amenity_osm_values']:
        amenity_df1 = access_layer1.loc[access_layer1.amenity == amenity].copy()
        amenity_df2 = access_layer2.loc[access_layer2.amenity == amenity].copy()

        # small buffer to keep correct geometry
        amenity_df1.geometry = amenity_df1.geometry.buffer(0.000001).copy()
        amenity_df2.geometry = amenity_df2.geometry.buffer(0.000001).copy()
        gdf1 = gpd.GeoDataFrame(amenity_df1, geometry='geometry')
        gdf2 = gpd.GeoDataFrame(amenity_df2, geometry='geometry')

        try:
            res_union = gpd.overlay(gdf1, gdf2, how='union')
        except AttributeError:
            pass

        # value means range value
        res_union['dif'] = res_union['value_2'] - res_union['value_1']
        # set the same crs as the city border holds
        res_union.crs = city_crs
        # intersect with jakarta border for consistency
        iso_intersected = gpd.overlay(res_union, city_border, how='intersection')

        iso_intersected.to_file(
            path.join(DATA_DIR, 'results/impact_maps/access_dif_' + scenario + '_' + amenity + '.shp'),
            driver='ESRI Shapefile')
