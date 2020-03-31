# -*- coding: utf-8 -*-
import networkit as nkit
import pandas as pd
from shapely.geometry import Point
from pprint import pprint


def calculate_centrality(graph, centrality_measure, normalized=True):
    """
    Converts networkx graph to networkit graph, calculates betweenness centrality with nkit and saves results in csv file.
    :param normalized:
    :param graph: network routing graph
    :type graph: networkx graph
    :param centrality_measure: networkit centrality measure
    :type centrality_measure: string
    :return: betweenness centrality dataframe
    """
    # convert networkx graph to networkit graph
    # nkg_centr = nkit.nxadapter.nx2nk(graph)
    nkg_centr = graph
    nkit.overview(nkg_centr)

    # define networkit centrality measure
    nkit_centrality = None
    column_declaration = None
    if centrality_measure == 'Betweenness':
        nkit_centrality = nkit.centrality.Betweenness(nkg_centr, normalized=normalized).run()
        column_declaration = 'btwn'
    elif centrality_measure == 'Harmonic_Closeness':
        # normalization only for unweighted graphs
        nkit_centrality = nkit.centrality.HarmonicCloseness(nkg_centr, normalized=normalized).run()
        column_declaration = 'cls'

    centrality_scores = nkit_centrality.scores()
    pprint(nkit_centrality.ranking()[:10])
    print('{} calculated'.format(centrality_measure))

    # create dataframe with new enum_id_centrality
    centrality_scores_df = pd.DataFrame(list(enumerate(centrality_scores)), columns=['enum_id_ce', column_declaration])

    return centrality_scores_df, centrality_scores


def restructure_dataframe(graph):
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

