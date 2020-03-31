# -*- coding: utf-8 -*-
from openrouteservice import client
from shapely.geometry import mapping, shape
from shapely import ops
import fiona as fn
import pandas as pd
import geopandas as gpd

# isochrone request
# clip with flood layer


def iso_request(api_key, amenities, output):
    """"""

    # using my local openrouteservice package with the manually created routing graph
    clnt = client.Client(base_url='http://localhost:8080/ors', key=api_key)

    request_counter = 0
    iso_geom_list = []
    for geom, amenity_type, amenity_id in zip(amenities['geometry'], amenities['amenity'], amenities['id']):
        point_geom = mapping(geom)

        params_iso = {'locations': [[point_geom['coordinates'][0], point_geom['coordinates'][1]]],
                      'profile': 'driving-car',
                      'interval': 300,  # 300/60 = 5 min
                      'range': [1800],  # 1800/60 = 30 min
                      'attributes': ['area'],
                      'smoothing': 0}

        try:
            iso_geom_list.append([clnt.isochrones(**params_iso), amenity_type, request_counter, amenity_id])
        except Exception:
            print(params_iso)
            pass
        request_counter += 1
    print('requested %s isochrones from ORS API' % request_counter)

    # save isochrones to shapefiles
    schema = {'geometry': 'Polygon',
              'properties': {'id': 'int',
                             'iso_id': 'int',
                             'amenity': 'str',
                             'amenity_id': 'str',
                             'value': 'int',
                             'area': 'float',
                             'center_x': 'float',
                             'center_y': 'float'}}

    index = 0
    with fn.open(output, 'w', 'ESRI Shapefile', schema) as c:
        for poly in iso_geom_list:
            iso = poly[0]
            iso_counter = poly[2]
            amenity = poly[1]
            amenity_id = poly[3]
            for range_iso in iso['features']:
                c.write({'geometry': range_iso['geometry'],
                         'properties': {'id': index,
                                        'iso_id': iso_counter,
                                        'amenity': amenity,
                                        'amenity_id': amenity_id,
                                        'value': range_iso['properties']['value'],
                                        'area': range_iso['properties']['area'],
                                        'center_x': range_iso['properties']['center'][0],
                                        'center_y': range_iso['properties']['center'][1], }})
                index += 1

    print('saved isochrones as shapefile.')


def flood_layer_union(flood_layer):
    # TODO: rewrite docstring -> fix..
    """Fix geometry to calculate difference overlay with border layer. Needed to select flooded amenities"""
    flood_geom = []
    for poly in range(len(flood_layer)):
        if flood_layer['geometry'][poly] is not None:
            flood_geom.append(shape(flood_layer['geometry'][poly]))
    union_l = ops.cascaded_union(flood_geom)
    # df = pd.DataFrame(union_l, columns=['geometry'])
    # geodf = gpd.GeoDataFrame(df, geometry='geometry')
    return union_l


def iso_flood_clip(iso_amenities, flood_data, output):
    """
    Clip flood areas out of isochrones, which were wrongly created due to simplification in isochrone algorithm.
    :param iso_amenities: created isochrones with amenities as center
    :param flood_data: floodprone or flood data
    :param output: relative output folder path
    :return: clipped isochrones as list
    """
    # flood_union = ops.cascaded_union(flood_data['geometry'])
    flood_union = flood_layer_union(flood_data)

    clipped_result = []
    try:
        for iso in iso_amenities:
            iso_geom = shape(iso['geometry'])
            iso_properties = list(iso['properties'].values())
            if iso_geom.intersects(flood_union):
                # if intersects, the isochrone difference will be added
                iso_dif = iso_geom.difference(flood_union)
                iso_properties.insert(0, iso_dif)
                clipped_result.append(iso_properties)
            else:
                # else, the complete isochrone will be added
                iso_properties.insert(0, iso_geom)
                clipped_result.append(iso_properties)
    except TypeError:
        pass

    iso_schema = iso_amenities.schema
    column_names = list(iso_schema['properties'].keys())
    column_names.insert(0, 'geometry')

    df = pd.DataFrame(clipped_result, columns=column_names)
    geodf = gpd.GeoDataFrame(df, geometry='geometry')
    geodf.to_file(output, driver='ESRI Shapefile')

    return clipped_result
