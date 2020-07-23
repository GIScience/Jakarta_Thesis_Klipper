# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from openrouteservice import client, exceptions
from ma_jakarta.scripts.data_preprocessing import floods
from shapely.geometry import mapping
import fiona as fn
import geopandas as gpd
from os import path, mkdir
import logging
import sys


class Isochrone:
    """"""

    def __init__(self, api_key, scenario):
        self.api_key = api_key
        self.scenario = scenario

    def iso_request(self, output):
        """Openrouteservice isochrone calculation"""

        print('Make sure to first build correct ORS graph! E.g. floodprone graph for floodprone isochrone request. \n'
              'Requesting isochrones...')

        # using my local openrouteservice package with the manually created routing graph
        clnt = client.Client(base_url='http://localhost:8080/ors', key=self.api_key)

        # health care locations as isochrone centers
        amenities = gpd.read_file(path.join(DATA_DIR, SETTINGS['amenities'][self.scenario]))

        # TODO: adjust for OSM and HOT data
        id_name = ['osm_way_id']
        # id_name = ['id_1' if scenario_name == 'normal' else 'id']
        request_counter = 0
        iso_geom_list = []

        for geom, amenity_type, amenity_id in zip(amenities['geometry'], amenities['amenity'], amenities[id_name[0]]):
            point_geom = mapping(geom)

            # isochrone parameters
            if self.scenario == 'normal':
                params_iso = {'locations': [[point_geom['coordinates'][0][0], point_geom['coordinates'][0][1]]],
                              'profile': 'driving-car',
                              'interval': 300,  # 300/60 = 5 min
                              'range': [1800],  # 1800/60 = 30 min
                              'attributes': ['area']}
            else:
                params_iso = {'locations': [[point_geom['coordinates'][0], point_geom['coordinates'][1]]],
                              'profile': 'driving-car',
                              'interval': 300,  # 300/60 = 5 min
                              'range': [1800],  # 1800/60 = 30 min
                              'attributes': ['area']}

            try:
                # request isochrones
                iso_geom_list.append([clnt.isochrones(**params_iso), amenity_type, request_counter, amenity_id])
            except exceptions.ApiError:
                print(params_iso, 'is isolated and out of routing graph range.')
                pass
            request_counter += 1

        print('Requested isochrones for %s healthsite locations from ORS API' % request_counter)

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
        with fn.open(output, 'w', 'ESRI Shapefile', schema) as out_file:
            for poly in iso_geom_list:
                iso = poly[0]
                iso_counter = poly[2]
                amenity = poly[1]
                amenity_id = poly[3]
                for range_iso in iso['features']:
                    out_file.write({'geometry': range_iso['geometry'],
                                    'properties': {'id': index,
                                                   'iso_id': iso_counter,
                                                   'amenity': amenity,
                                                   'amenity_id': amenity_id,
                                                   'value': range_iso['properties']['value'],
                                                   'area': range_iso['properties']['area'],
                                                   'center_x': range_iso['properties']['center'][0],
                                                   'center_y': range_iso['properties']['center'][1], }})
                    index += 1

    def flood_difference(self, iso_dissolved, output):
        """Calculates difference of isochrones and flood areas.
        Needed due to wrongly created areas due to simplification in isochrone algorithm."""
        flood_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed'][self.scenario]))
        flood_union = floods.flood_union(flood_data)

        iso_intersected = gpd.overlay(iso_dissolved, flood_union, how='difference')
        iso_intersected.to_file(output, driver='ESRI Shapefile')


if __name__ == '__main__':
    scenario_name = None
    ors_api_key = None

    try:
        scenario_name = str(sys.argv[1])  # e.g. floodprone
        ors_api_key = str(SETTINGS['ors_api_key'])
    except IndexError:
        logging.error('Please provide a valid openrouteservice api key (Register for free: '
                      'https://openrouteservice.org/dev/#/signup) and a scenario name like "floodprone".')
        exit()

    if not path.exists(path.join(DATA_DIR, 'results')):
        mkdir(path.join(DATA_DIR, 'results'))

    isochrone_output = path.join(DATA_DIR, 'results', 'iso_' + scenario_name + '.shp')
    ors_iso = Isochrone(ors_api_key, scenario_name)

    if not path.exists(isochrone_output):
        if scenario_name != 'normal':
            preprocess_output = path.join(DATA_DIR, 'preprocessed', 'iso_pre_' + scenario_name + '.shp')
            ors_iso.iso_request(preprocess_output)
            # flood_difference optional -> speed up calculation vs. more accurate calculation
            ors_iso.flood_difference(gpd.read_file(preprocess_output), isochrone_output)
        else:
            ors_iso.iso_request(isochrone_output)
    else:
        print(isochrone_output, 'already exists.')
