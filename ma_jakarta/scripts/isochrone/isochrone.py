# -*- coding: utf-8 -*-
from __init__ import DATA_DIR, SETTINGS
from openrouteservice import client, exceptions
from ma_jakarta.scripts.data_preprocessing import floods, admin_border
from shapely.geometry import mapping, Polygon
import geopandas as gpd
import pandas as pd
from os import path, mkdir
import logging
import sys


class Isochrone:
    """Isochrone request for catchment areas"""

    def __init__(self, api_key, scenario):
        self.api_key = api_key
        self.scenario = scenario

    def iso_request(self, amenities, city_border):
        """Openrouteservice isochrone calculation"""

        print('Make sure to first build correct ORS graph! E.g. normal graph for normal isochrone request. \n'
              'Requesting isochrones...')

        # using local openrouteservice package with the manually created routing graph
        clnt = client.Client(base_url='http://localhost:8080/ors', key=self.api_key)

        # osm data id = id_1; hot data id = osm_id
        id_name = ['id_1' if 'id_1' in amenities else 'osm_id'][0]
        iso_range_values = SETTINGS['iso_range_values']
        request_counter = 0
        iso_df_list = []

        for geom, amenity_type, amenity_id in zip(amenities['geometry'], amenities['amenity'], amenities[id_name]):
            point_geom = mapping(geom)

            # isochrone parameters
            params_iso = {'locations': [[point_geom['coordinates'][0], point_geom['coordinates'][1]]],
                          'profile': 'driving-car',
                          'interval': iso_range_values[0],
                          'range': [iso_range_values[-1]]}

            try:
                # request isochrones
                iso_df = pd.DataFrame.from_dict(clnt.isochrones(**params_iso)['features'])
                # adjust geometry column for geopandas dataframe
                iso_df['geometry'] = [Polygon(g['coordinates'][0]) for g in iso_df['geometry']]
                # add additional data
                iso_df['value'] = [g['value'] for g in iso_df['properties']]
                iso_df['amenity'] = amenity_type
                iso_df['iso_id'] = request_counter
                iso_df['amenity_id'] = amenity_id
                iso_df_list.append(iso_df)

            except exceptions.ApiError:
                print(params_iso, 'is isolated and out of routing graph range.')
                pass
            request_counter += 1

        print('Requested isochrones for %s healthsite locations from ORS API' % request_counter)

        all_isochrones = pd.concat([layer for layer in iso_df_list])
        all_isochrones = gpd.GeoDataFrame(all_isochrones, geometry='geometry')

        return all_isochrones


if __name__ == '__main__':
    scenario_input = None
    hot_data = None

    try:
        scenario_input = str(sys.argv[1])
    except IndexError:
        logging.error('Please provide a valid scenario name like "normal" or "flooded".')
        sys.exit(1)

    if SETTINGS['ors_api_key'] is None:
        print('Please provide a valid openrouteservice api key (Register for free: '
              'https://openrouteservice.org/dev/#/signup).')
        sys.exit(1)
    else:
        ors_api_key = str(SETTINGS['ors_api_key'])

    output_path = str(path.join(DATA_DIR, SETTINGS['isochrones']['path']))
    if not path.exists(output_path):
        mkdir(output_path)

    ors_iso = Isochrone(ors_api_key, scenario_input)

    # health care locations as isochrone centers
    amenities_input = gpd.read_file(path.join(DATA_DIR, SETTINGS['amenities'][scenario_input]))
    city_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['city_border']['preprocessed']))
    data_output_path = path.join(DATA_DIR, SETTINGS['isochrones'][scenario_input])

    if not path.exists(data_output_path):
        if scenario_input == 'flooded':
            flood_layer = gpd.read_file(path.join(DATA_DIR, SETTINGS['flood']['preprocessed']))
            iso_request_result = ors_iso.iso_request(amenities_input, city_layer)
            iso_request_result.to_file(path.join(DATA_DIR, SETTINGS['isochrones']['pre_flooded']), driver='ESRI Shapefile')
            print(path.join(DATA_DIR, SETTINGS['isochrones']['pre_flooded']), 'saved.')

            # calculate city difference to receive only data within the city
            iso_geom_city = admin_border.border_intersect(city_layer, iso_request_result)
            # remove flood areas due to simplification
            iso_result = floods.flood_difference(iso_geom_city, flood_layer)
            iso_result.to_file(path.join(DATA_DIR, SETTINGS['isochrones']['flooded']), driver='ESRI Shapefile')
            print(path.join(DATA_DIR, SETTINGS['isochrones']['flooded']), 'saved.')
        else:
            iso_result = ors_iso.iso_request(amenities_input, city_layer)
            iso_result.to_file(path.join(DATA_DIR, SETTINGS['isochrones']['normal']), driver='ESRI Shapefile')
            print(path.join(DATA_DIR, SETTINGS['isochrones']['normal']), 'saved.')
    else:
        print(output_path, 'already exists.')
