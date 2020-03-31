# -*- coding: utf-8 -*-
import networkit as nkit
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from os import path
from pprint import pprint
import logging


class Centrality:
    """"""

    def __init__(self, graph, centrality_measure, normalized=True):
        self.graph = graph
        self.centrality_measure = centrality_measure
        self.normalized = normalized

    @classmethod
    def calculate_centrality(cls, centrality_measure, graph, normalized):
        """
        Converts networkx graph to networkit graph, calculates betweenness centrality with nkit and saves results in csv file.
        :param normalized:
        :param graph: network routing graph
        :type graph: NetworKit graph
        :param centrality_measure: networkit centrality measure
        :type centrality_measure: string
        :return: betweenness centrality dataframe
        """
        # convert networkx graph to networkit graph
        # nkg_centr = nkit.nxadapter.nx2nk(graph)

        # define networkit centrality measure
        nkit_centrality = None
        column_declaration = None
        if centrality_measure == 'Betweenness':
            nkit_centrality = nkit.centrality.Betweenness(graph, normalized=normalized).run()
            column_declaration = 'btwn'
        elif centrality_measure == 'Harmonic_Closeness':
            # normalization only for unweighted graphs
            nkit_centrality = nkit.centrality.HarmonicCloseness(graph, normalized=normalized).run()
            column_declaration = 'cls'

        centrality_scores = nkit_centrality.scores()
        pprint(nkit_centrality.ranking()[:10])
        print('{} calculated'.format(centrality_measure))

        # create dataframe with new enum_id_centrality
        centrality_scores_df = pd.DataFrame(list(enumerate(centrality_scores)), columns=['enum_id_ce', column_declaration])

        return centrality_scores_df, column_declaration  #, centrality_scores

    @classmethod
    def restructure_dataframe(cls, graph):
        """
        Restructures node data to dataframe by enumerating node elements, inserting data to new created column 'enum_id'
        and converting node geometry to shapely Point.
        :param graph: osmnx or networkx network graph
        :return: restructured node data dataframe
        """
        node_data = list(graph.nodes(data=True))
        node_data_restructured = []
        node_counter = 0
        if 'geometry' not in node_data[0][1].keys():
            for node in range(len(node_data)):
                # Add enumerate attribute to node_data
                if 'enum_id_ce' not in node_data[node][1].keys():
                    node_data[node][1]['enum_id_ce'] = node_counter
                # Restructure geometry and convert it to shapely Point
                node_data[node][1]['geometry'] = Point(node_data[node][0])
                node_data_restructured.append(node_data[node][1])
                node_counter += 1
        else:
            # if already restructured because of previous centrality calculations
            for node in range(len(node_data)):
                node_data_restructured.append(node_data[node][1])

        column_names = node_data[0][1].keys()

        # create dataframe
        node_data_df = pd.DataFrame(node_data_restructured, columns=list(column_names))

        return node_data_df

    @classmethod
    def save(cls, graph, column_declaration, centrality_df, graph_df):
        """Join dataframes and save as shapefile."""
        df = graph_df.merge(centrality_df, on='enum_id_ce')
        geodf = gpd.GeoDataFrame(df, geometry='geometry')
        geodf.to_file(path.join(graph, 'node_' + column_declaration + '.shp'), driver='ESRI Shapefile')  # path.join(BASEDIR, 'graphs_weighted/flooded/nodes_harmcls.shp'

        return geodf

    def run(self):
        """"""
        centrality_df, column_declaration = self.calculate_centrality(self.centrality_measure, self.graph, self.normalized)
        graph_df = self.restructure_dataframe(self.graph)
        geodf_graph = self.save(self.graph, column_declaration, centrality_df, graph_df)
        logging.info(self.centrality_measure, 'saved in', path.join(self.graph, 'node_' + column_declaration + '.shp'))

        return geodf_graph
