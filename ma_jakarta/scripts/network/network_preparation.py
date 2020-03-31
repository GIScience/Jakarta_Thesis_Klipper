# -*- coding: utf-8 -*-
import osmnx as ox
import networkx as nx
import rtree
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, LineString, Point
from shapely import ops


def download_network(city_name, network_type, network_file_name, output_path):
    """Download and save network road graph with OSMnx module."""

    ox_graph = ox.graph_from_place(city_name, network_type=network_type)
    ox.save_graph_shapefile(ox_graph, network_file_name, output_path)

    return ox_graph


def flood_layer_union(flood_layer):
    # TODO: rewrite docstring -> fix..
    """Fix geometry to calculate difference overlay with border layer. Needed to select flooded amenities"""

    flood_geom = []
    for poly in range(len(flood_layer)):
        if flood_layer['geometry'][poly] is not None:
            flood_geom.append(shape(flood_layer['geometry'][poly]))
    union_l = ops.cascaded_union(flood_geom)

    # TODO: here geodataframe needed?
    df = pd.DataFrame(union_l, columns=['geometry'])
    geodf = gpd.GeoDataFrame(df, geometry='geometry')

    return geodf


def flood_intersection(graph, flood_layer, output):
    """
        Intersects network routing graph with flood polygons and removes edges and nodes which are affected by flood.
        :param graph: graph of complete area
        :type graph: osmnx or networkx network routing graph with edge and node file
        :param flood_layer: areas which are flooded
        :type flood_layer: polygon shapefile
        :param output: folder path to save output
        :type output: string
        :return: flood networkx graph
        """
    flood_data = flood_layer_union(flood_layer)

    edge_data = list(graph.edges(data=True))

    # create an empty spatial index object
    index = rtree.index.Index()
    counter = 0
    for edge in range(len(edge_data)):
        edge_geom = shape(LineString([Point(edge_data[edge][0]), Point(edge_data[edge][1])]))
        index.insert(counter, edge_geom.bounds)
        counter += 1

    # check intersection and remove affected nodes
    intersect_counter = 0
    for poly in flood_data['geometry']:
        for fid in list(index.intersection(shape(poly).bounds)):
            edge_geom_shape = shape(LineString([Point(edge_data[fid][0]), Point(edge_data[fid][1])]))
            if edge_geom_shape.intersects(shape(poly)):
                e = edge_data[fid][0]
                e_to = edge_data[fid][1]
                # remove intersected edges
                if graph.has_edge(e, e_to):
                    graph.remove_edge(e, e_to)
                # remove intersected nodes
                if Point(edge_data[fid][0]).intersects(shape(poly)) and graph.has_node(e):
                    graph.remove_node(e)
                    intersect_counter += 1
                if Point(edge_data[fid][1]).intersects(shape(poly)) and graph.has_node(e_to):
                    graph.remove_node(e_to)
                    intersect_counter += 1
    print('Amount of intersected and removed nodes:', intersect_counter)

    # save networkx graph with complete graph enum_id
    try:
        nx.write_shp(graph, output)
    except Exception as err:
        print(err)
    print('Intersected networkx graph saved')

    return graph
