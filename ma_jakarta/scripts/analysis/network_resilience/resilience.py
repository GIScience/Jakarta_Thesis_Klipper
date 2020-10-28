from __init__ import SETTINGS, DATA_DIR
from os import path
import geopandas as gpd
import pandas as pd
import sys
import logging


def top_x_nodes(centrality, percent, notnull=True):
    """Calculates one or ten percent of total node amount"""
    centrality_acronym = None
    column_normal = None
    column_flooded = None

    if centrality == 'betweenness' or centrality == 'Betweenness' or centrality == 'btwn':
        centrality_acronym = 'btwn'
        column_normal = 'btwn_n'
        column_flooded = 'btwn_f'
    elif centrality == 'closeness' or centrality == 'Closeness' or centrality == 'cls':
        centrality_acronym = 'cls'
        column_normal = 'cls_n'
        column_flooded = 'cls_f'

    # file consists of all nodes within normal scenario
    node_df = gpd.read_file(path.join(DATA_DIR, SETTINGS['networks'][centrality_acronym + '_dif']))
    # select best rated one/ten percent -> one/ten percent of total amount
    normal_top_x = node_df.nlargest(int(len(node_df) * (percent / 100)), column_normal)
    flooded_top_x = node_df.nlargest(int(len(node_df) * (percent / 100)), column_flooded)

    # 'in_n_f' = in normal and flooded foreground network
    normal_top_x.loc[normal_top_x.osmid.isin(flooded_top_x.osmid), 'in_n_f'] = normal_top_x[
        centrality_acronym + '_dif']

    if notnull is True:
        # if node is flooded = -999
        normal_top_x.loc[pd.isna(normal_top_x[column_flooded]), 'in_n_f'] = -999
        # if node is not flooded but not in top x percent
        normal_top_x['in_n_f'].fillna(999, inplace=True)

    geodf = gpd.GeoDataFrame(normal_top_x, geometry='geometry')
    geodf.to_file(path.join(DATA_DIR,
                            'results/flooded', 'nodes_' + centrality_acronym + '_top_' + str(percent) + '.shp'),
                  driver='ESRI Shapefile')

    return normal_top_x


def sameness(normal_top_ten, centrality):
    """Modified sameness ratio calculation for network resilience. Based on the idea by
        Abshirini, Ehsan, and Daniel Koch. 2017.
        “Resilience, Space Syntax and Spatial Interfaces: The Case of River Cities.” A/Z :
        ITU Journal of Faculty of Architecture 14 (1): 25–41. https://doi.org/10.5505/itujfa.2017.65265."""

    # nodes which are flooded or not in the top x percent
    not_top = len(normal_top_ten[normal_top_ten.in_n_f == 999]) + len(normal_top_ten[normal_top_ten.in_n_f == -999])

    amount_normal_top = len(normal_top_ten)
    amount_normal_in_flooded_top = len(normal_top_ten) - not_top
    sameness_ratio = ((100 / amount_normal_top) * amount_normal_in_flooded_top) / 100

    print('Sameness', centrality, 'Ratio:', sameness_ratio)


if __name__ == '__main__':

    centrality_input = None

    try:
        centrality_input = str(sys.argv[1])
    except KeyError:
        logging.error('Please provide one centrality name, e.g., Betweenness or Closeness.')

    if 'Betweenness' not in centrality_input and 'Closeness' not in centrality_input:
        logging.error('Please provide one centrality name, e.g. Betweenness or Closeness.')
        exit()

    top_x_nodes(centrality_input, 1)
    top_10_percent_nodes = top_x_nodes(centrality_input, 10)
    print('column name in_n_f = in normal and flooded foreground network \n'
          '-999 = node is flooded \n999 = node is not flooded but not in top x percent')
    sameness(top_10_percent_nodes, centrality_input)
