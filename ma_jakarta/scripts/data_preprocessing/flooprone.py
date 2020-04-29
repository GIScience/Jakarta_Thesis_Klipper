# -*- coding: utf-8 -*-
import fiona as fn


def floodprone_selection(flood_layer, output=None):
    """Select and save floodprone related features."""

    prone_features = []
    for feature in flood_layer:
        feat_properties = dict(feature['properties'].items())
        if feat_properties['flood_prone'] == 'yes':
            prone_features.append(feature)

    if output is not None:
        with fn.open(output, 'w', driver='ESRI Shapefile', schema=flood_layer.schema) as o_shp:
            for prone_feat in prone_features:
                o_shp.write(prone_feat)
