# -*- coding: utf-8 -*-
from ma_jakarta.scripts.data_preprocessing import floods
from shapely.geometry import shape
import geopandas as gpd
import pandas as pd
import logging

# TODO: add all attributes to selected


class Amenities:
    """Amenity data preparation"""

    def __init__(self, amenities, border):
        self.amenities = amenities
        self.border = border

    def preprocessing(self, amenities_output):
        """Calculate amenities centroid, select objects laying within administrative border, save locally"""

        amenities_centroid = self.calculate_centroid()
        amenities_geodf = self.create_geodataframe(amenities_centroid)
        jakarta_amenities = self.intersect_with_border(amenities_geodf, amenities_output)

        logging.info(amenities_output, 'saved')

        return jakarta_amenities

    def calculate_centroid(self):
        """"""
        centroid_feature = []
        for feature in self.amenities:
            feat_geometry = feature['geometry']
            feat_properties = list(feature['properties'].values())
            centroid = shape(feat_geometry).centroid
            feat_properties.insert(0, centroid)
            centroid_feature.append(feat_properties)

        return centroid_feature

    def create_geodataframe(self, centroid_feature):
        """Save shapefile locally."""

        schema = self.amenities.schema
        column_names = list(schema['properties'].keys())
        column_names.insert(0, 'geometry')

        df = pd.DataFrame(centroid_feature, columns=column_names)
        geodf = gpd.GeoDataFrame(df, geometry='geometry')

        return geodf

    def intersect_with_border(self, amenities_centroid, amenities_output):
        """Select amenities which are within the administrative jakarta border."""

        intersected_amenities = gpd.overlay(amenities_centroid, self.border, how='intersection')
        intersected_amenities.to_file(amenities_output, driver='ESRI Shapefile')

        return intersected_amenities

    def select_amenities(self, amenities, flood_layer, output):
        """Select floodprone and flood related amenities"""

        flood_union = floods.flood_union(flood_layer)
        # not_flooded = gpd.overlay(self.border, r, how='difference')

        selected_amenities = gpd.overlay(amenities, flood_union, how='difference')

        # df = pd.DataFrame(selected_amenities, columns=['id', 'geometry', 'amenity'])
        # geodf = gpd.GeoDataFrame(df, geometry='geometry')
        selected_amenities.to_file(output, driver='ESRI Shapefile')

        logging.info(output, 'saved with', len(selected_amenities), 'selected amenities')

        return selected_amenities
