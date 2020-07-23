# -*- coding: utf-8 -*-
from __init__ import SETTINGS, DATA_DIR
from os import path
import geopandas as gpd
import pandas as pd
import logging


class HotAmenities:
    """Data preparation for HOT provided healthcare data"""

    def __init__(self, amenities):
        self.amenities = amenities

    def categorize_capacity(self, row):

        if row['capacity_p'] is None:
            val = None
        elif (row['capacity_p'] == '>10') or (row['capacity_p'] == '20') or (row['capacity_p'] == '30') or \
                (row['capacity_p'] == '25') or (row['capacity_p'] == '<50'):
            val = '<50'
        elif (row['capacity_p'] == '50') or (row['capacity_p'] == '80') or (row['capacity_p'] == '97') or (
                row['capacity_p'] == '100') or \
                (row['capacity_p'] == '50-100'):
            val = '50-100'
        elif (row['capacity_p'] == '>100') or (row['capacity_p'] == '100-200') or (row['capacity_p'] == '150') or \
                (row['capacity_p'] == '170') or (row['capacity_p'] == '200') or (row['capacity_p'] == '100-250') or \
                (row['capacity_p'] == '>100'):
            val = '101-250'
        elif (row['capacity_p'] == '300') or (row['capacity_p'] == '378') or (row['capacity_p'] == '250-500') or (
                row['capacity_p'] == '500'):
            val = '251-500'
        elif row['capacity_p'] == '>500':
            val = '>500'
        else:
            val = 'else'

        return val

    def cap_mean(self, input_df):
        """Define approx. bed amount of all given value ranges to fill null values """

        hs_mean = 0
        counter = 0
        for row in input_df['capacity_p']:
            if row is not None:
                if '-' in row:
                    first, second = row.split('-')
                    hs_mean += (int(first) + int(second)) / 2
                    counter += 1
                elif '>' in row:
                    val = int(row.split('>')[1])
                    hs_mean += (val + (val * 0.1))
                    counter += 1
                elif '<' in row:
                    val = int(row.split('<')[1])
                    hs_mean += (val - (val * 0.1))
                    counter += 1
                else:
                    val = int(row)
                    hs_mean += val
                    counter += 1

        return round(hs_mean / counter)

    def cap_value(self, input_df):
        """Define approx. bed amount for each value range"""

        value_list = []

        for row_id, row_cap in zip(input_df['osm_way_id'], input_df['capacity_p']):
            if row_cap is not None:
                if '-' in row_cap:
                    first, second = row_cap.split('-')
                    value_list.append([row_id, int((int(first) + int(second)) / 2)])
                elif '>' in row_cap:
                    val = int(row_cap.split('>')[1])
                    value_list.append([row_id, int((val + (val * 0.1)))])
                elif '<' in row_cap:
                    val = int(row_cap.split('<')[1])
                    value_list.append([row_id, int((val - (val * 0.1)))])
                else:
                    val = int(row_cap)
                    value_list.append([row_id, val])

        value_df = pd.DataFrame(value_list, columns=['osm_way_id', 'cap_int'])

        result_df = input_df.merge(value_df, on='osm_way_id')

        return result_df

    def run_capacity(self, scenario):
        hosp = self.amenities.loc[self.amenities.amenity == 'hospital']
        nan_hosp_mean = self.cap_mean(hosp)
        hosp['capacity_p'].fillna(str(nan_hosp_mean), inplace=True)

        clinic = self.amenities.loc[self.amenities.amenity == 'clinic']
        nan_clinic_mean = self.cap_mean(clinic)
        clinic['capacity_p'].fillna(str(nan_clinic_mean), inplace=True)

        complete_df = pd.concat([hosp, clinic])

        extended_df = complete_df.assign(cap_cat=complete_df.apply(self.categorize_capacity, axis=1))

        cap_df = self.cap_value(extended_df)
        geodf = gpd.GeoDataFrame(cap_df, geometry='geometry')
        geodf.to_file(path.join(DATA_DIR, SETTINGS['amenities'][scenario]), driver='ESRI Shapefile')

        logging.info(geodf, 'saved')

        return geodf
