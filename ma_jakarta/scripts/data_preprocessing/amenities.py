# -*- coding: utf-8 -*-
import rtree
from shapely.geometry import Point, shape
from shapely import ops
import geopandas as gpd
import pandas as pd
import logging


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

    @ classmethod
    def flood_layer_union(cls, flood_layer):
        # TODO: rewrite docstring -> fix..
        """Fix geometry to calculate difference overlay with border layer. Needed to select flooded amenities"""

        flood_geom = []
        for poly in range(len(flood_layer)):
            if flood_layer['geometry'][poly] is not None:
                flood_geom.append(shape(flood_layer['geometry'][poly]))
        union_l = ops.cascaded_union(flood_geom)

        df = pd.DataFrame(union_l, columns=['geometry'])
        geodf = gpd.GeoDataFrame(df, geometry='geometry')

        return geodf

    def select_amenities(self, amenities, flood_layer, output):
        """Select floodprone and flood related amenities"""

        r = self.flood_layer_union(flood_layer)
        not_flooded = gpd.overlay(self.border, r, how='difference')

        # create an empty spatial index object
        index = rtree.index.Index()
        counter = 0
        for amenity in range(len(amenities)):
            amenity_geom = shape(Point(amenities['geometry'][amenity]))
            index.insert(counter, amenity_geom.bounds)
            counter += 1

        # check intersection and remove affected nodes
        selected_amenities = []
        intersect_counter = 0
        for poly in not_flooded['geometry']:
            for fid in list(index.intersection(shape(poly).bounds)):
                amenity_geom_shape = shape(Point(amenities['geometry'][fid]))
                if amenity_geom_shape.intersects(shape(poly)):
                    selected_amenities.append(
                        [amenities['id_1'][fid], amenities['geometry'][fid], amenities['amenity'][fid]])
                    intersect_counter += 1

        df = pd.DataFrame(selected_amenities, columns=['id', 'geometry', 'amenity'])
        geodf = gpd.GeoDataFrame(df, geometry='geometry')
        geodf.to_file(output, driver='ESRI Shapefile')

        logging.info(output, 'saved with', intersect_counter, 'selected amenities')

        return selected_amenities
