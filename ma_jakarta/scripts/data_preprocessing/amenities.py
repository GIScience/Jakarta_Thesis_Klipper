# -*- coding: utf-8 -*-
from __init__ import border_crs
from shapely.geometry import shape
import geopandas as gpd
import pandas as pd


class Amenities:
    """Amenity data preparation"""

    def __init__(self, amenities, border):
        self.amenities = amenities
        self.border = border

    def preprocessing(self):
        """Calculate centroids of amenities and select objects laying within administrative border"""

        amenities_centroid = self.calculate_centroid()
        amenities_geodf = self.create_geodataframe(amenities_centroid)
        jakarta_amenities = self.intersect_with_border(amenities_geodf)

        return jakarta_amenities

    def calculate_centroid(self):
        """Calculate centroids of amenities"""
        centroid_feature = []
        for feature in self.amenities:
            feat_geometry = feature['geometry']
            feat_properties = list(feature['properties'].values())
            centroid = shape(feat_geometry).centroid
            feat_properties.insert(0, centroid)
            centroid_feature.append(feat_properties)

        return centroid_feature

    def create_geodataframe(self, centroid_feature):
        """Convert dataframe to geodataframe"""

        schema = self.amenities.schema
        column_names = list(schema['properties'].keys())
        column_names.insert(0, 'geometry')

        df = pd.DataFrame(centroid_feature, columns=column_names)
        geodf = gpd.GeoDataFrame(df, geometry='geometry')

        return geodf

    def intersect_with_border(self, amenities_centroid):
        """Select amenities which are within the administrative city border"""

        amenities_centroid.crs = border_crs
        self.border.crs = amenities_centroid.crs
        intersected_amenities = gpd.overlay(amenities_centroid, self.border, how='intersection')

        return intersected_amenities

    def select_amenities(self, amenities, flood_layer):
        """Select not flooded related amenities"""

        selected_amenities = gpd.overlay(amenities, flood_layer, how='difference')

        return selected_amenities
