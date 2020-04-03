# -*- coding: utf-8 -*-
from __init__ import BASEDIR, DATA_DIR, SETTINGS
from openrouteservice import client, exceptions
from shapely.geometry import mapping, shape
from shapely import ops
import fiona as fn
import pandas as pd
import geopandas as gpd
from os import path
import logging
import sys


class Isochrone:
    """"""

    def __init__(self, api_key, scenario):
        self.api_key = api_key
        self.scenario = scenario

    def iso_request(self, output):
        """"""

        print('Make sure to first build correct ORS graph! E.g. floodprone graph for floodprone isochrone request.')

        amenities = gpd.read_file(path.join(DATA_DIR, SETTINGS['amenities_' + self.scenario]))

        # using my local openrouteservice package with the manually created routing graph
        clnt = client.Client(base_url='http://localhost:8080/ors', key=self.api_key)

        request_counter = 0
        iso_geom_list = []
        for geom, amenity_type, amenity_id in zip(amenities['geometry'], amenities['amenity'], amenities['id']):
            point_geom = mapping(geom)

            params_iso = {'locations': [[point_geom['coordinates'][0], point_geom['coordinates'][1]]],
                          'profile': 'driving-car',
                          'interval': 300,  # 300/60 = 5 min
                          'range': [1800],  # 1800/60 = 30 min
                          'attributes': ['area']}

            try:
                iso_geom_list.append([clnt.isochrones(**params_iso), amenity_type, request_counter, amenity_id])
            except exceptions.ApiError:
                print(params_iso, 'is isolated and out of routing graph range.')
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

    @ staticmethod
    def flood_layer_union(flood_layer):
        # TODO: rewrite docstring -> fix..
        """Fix geometry to calculate difference overlay with border layer. Needed to select flooded amenities"""
        flood_geom = []
        for poly in range(len(flood_layer)):
            if flood_layer['geometry'][poly] is not None:
                flood_geom.append(shape(flood_layer['geometry'][poly]))
        union_l = ops.cascaded_union(flood_geom)
        return union_l

    def iso_flood_intersect(self, preprocessed_iso, output):  # iso_amenities, flood_data, output
        """
        Intersect flood areas out of isochrones, which were wrongly created due to simplification in isochrone algorithm.
        :param preprocessed_iso: created isochrones with amenities as center
        :param output: relative output folder path
        :return: clipped isochrones as list
        """
        print('Starting to intersect isochrone layer with flood layer. Go and get a coffee..')
        flood_data = gpd.read_file(path.join(DATA_DIR, SETTINGS[self.scenario]))
        flood_union = self.flood_layer_union(flood_data)

        requested_isochrones = fn.open(preprocessed_iso)

        clipped_result = []
        try:
            for iso in requested_isochrones:
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

        iso_schema = requested_isochrones.schema
        column_names = list(iso_schema['properties'].keys())
        column_names.insert(0, 'geometry')

        df = pd.DataFrame(clipped_result, columns=column_names)
        geodf = gpd.GeoDataFrame(df, geometry='geometry')
        geodf.to_file(output, driver='ESRI Shapefile')

        return clipped_result


if __name__ == '__main__':
    try:
        ors_api_key = str(sys.argv[1])
        scenario_name = str(sys.argv[2])  # e.g. floodprone
    except IndexError:
        logging.error('Please provide a valid openrouteservice api key (Register for free: '
                      'https://openrouteservice.org/dev/#/signup) and a scenario name like "floodprone".')

    output_file = path.join(DATA_DIR, 'results', 'iso_' + scenario_name + '.shp')
    ors_iso = Isochrone(ors_api_key, scenario_name)

    if not path.exists(output_file):
        if scenario_name != 'normal':
            print('Starting...')
            preprocess_path = path.join(DATA_DIR, 'preprocessed', 'iso_pre_' + scenario_name + '.shp')
            ors_iso.iso_request(preprocess_path)
            ors_iso.iso_flood_intersect(preprocess_path, output_file)
        else:
            ors_iso.iso_request(output_file)
    else:
        print(output_file, 'already exists.')
