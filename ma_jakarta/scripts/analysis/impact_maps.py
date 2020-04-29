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
        dif_geom = []
        amenity_df = iso_df.loc[iso_df['amenity'] == amenity]
        for i in range(len(amenity_df)):
            if i == 0:  # value = 300
                dif_geom.append([amenity_df.loc[i]['value'], amenity_df.loc[i]['geometry'], amenity_df.loc[i]['id'],
                                 amenity_df.loc[i]['iso_id'], amenity_df.loc[i]['amenity']])
            else:
                dif_geom.append([amenity_df.loc[i]['value'],
                                 amenity_df.loc[i]['geometry'].difference(amenity_df.loc[i - 1]['geometry']),
                                 amenity_df.loc[i]['id'], amenity_df.loc[i]['iso_id'], amenity_df.loc[i]['amenity']])

        amenity_df_modi = pd.DataFrame(dif_geom, columns=['value', 'geometry', 'id', 'iso_id', 'amenity'])
        amenity_geodf = gpd.GeoDataFrame(amenity_df_modi, geometry='geometry')
        punched_dir.append(amenity_geodf)

    punched_result = pd.concat([layer for layer in punched_dir])
    punched_result['scenario'] = scenario

    return punched_result


def union_access(access_layer1, access_layer2, scenario):
    """Union overlay of complete and flood layer to calculate the range value change of healthsites isochrones."""
    jakarta_border = gpd.read_file(path.join(DATA_DIR, SETTINGS['jakarta_border']))

    for amenity in SETTINGS['amenity_osm_values']:
        amenity_df1 = access_layer1.loc[access_layer1['amenity'] == amenity]
        amenity_df2 = access_layer2.loc[access_layer2['amenity'] == amenity]

        # small buffer to keep correct geometry
        amenity_df1['geometry'] = amenity_df1['geometry'].buffer(0.000001)
        amenity_df2['geometry'] = amenity_df2['geometry'].buffer(0.000001)
        gdf1 = gpd.GeoDataFrame(amenity_df1, geometry='geometry')
        gdf2 = gpd.GeoDataFrame(amenity_df2, geometry='geometry')

        res_union = gpd.overlay(gdf1, gdf2, how='union')
        # value means range value
        res_union['dif'] = res_union['value_2'] - res_union['value_1']
        # intersect with jakarta border for consistency
        iso_intersected = gpd.overlay(res_union, jakarta_border, how='intersection')
        iso_intersected.to_file(path.join(DATA_DIR, 'scratch/access_diff_' + scenario + '_' + amenity + '.shp'),
                                driver='ESRI Shapefile')
        print(DATA_DIR + 'scratch/access_diff_' + scenario + '_' + amenity + '.shp saved')
