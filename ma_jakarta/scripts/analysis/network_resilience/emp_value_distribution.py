from __init__ import SETTINGS, DATA_DIR
from os import path, mkdir
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import math
import copy
import sys
import logging


def autolabel(rects, ax, color):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', rotation=90, color=color)


def histogram_centrality(acronym, axis_label, round_value, first_scenario, second_scenario=None):
    """Creates histogram with normal and flooded centrality node values"""
    data_color = SETTINGS['data_color']
    n_bins = 10
    bin_edges = []
    label_list = []
    fig, ax = plt.subplots()

    # Plot the figure
    first_centrality = gpd.read_file(path.join(DATA_DIR, SETTINGS['networks'][first_scenario]))
    first_color = [data_color['normal'] if first_scenario == 'normal' else data_color['flooded']][0]

    min_bin_edge = first_centrality[acronym].max()/10
    for i in range(0, n_bins+1):
        # define equal bin edges
        bin_edges.append(min_bin_edge * i)
        if i < n_bins:
            # define bin labels
            label_list.append(str(round(min_bin_edge * i, round_value)) + ' - ' +
                              str(round(min_bin_edge * (i + 1), round_value)))
    width = min_bin_edge / 3

    # sort dataframe values in bins
    first_bin_amount = pd.cut(first_centrality[acronym], bins=bin_edges,
                              include_lowest=True).value_counts().reset_index()
    first_bin_amount = first_bin_amount.iloc[first_bin_amount['index'].cat.codes.argsort()]

    # create histogram entry
    rects1 = ax.bar(np.array(bin_edges[1:]) - width / 2, first_bin_amount[acronym], width,
                    label=first_scenario + ' scenario', color=first_color, edgecolor='black', linewidth=0.4)
    autolabel(rects1, ax, first_color)

    if second_scenario is not None:
        second_centrality = gpd.read_file(path.join(DATA_DIR, SETTINGS['networks'][second_scenario]))
        second_color = [data_color['normal'] if second_scenario == 'normal' else data_color['flooded']][0]

        # redefine histogram properties in case that disaster values increases
        if second_centrality[acronym].max() > first_centrality[acronym].max():
            # calculate increase difference
            cent_dif = second_centrality[acronym].max() - first_centrality[acronym].max()
            # calculate new amount of histogram value bins
            n_bins_extended = n_bins + math.ceil(cent_dif / min_bin_edge)
            # create deeopcopies to keep properties of normal scenario
            bin_edges_extended = copy.deepcopy(bin_edges)
            label_list_extended = copy.deepcopy(label_list)
            # create new properties
            for i in range(n_bins+1, n_bins_extended+1):
                bin_edges_extended.append(min_bin_edge * i)
            for i in range(n_bins, n_bins_extended):
                label_list_extended.append(str(round(min_bin_edge * i, round_value)) + ' - ' +
                                           str(round(min_bin_edge * (i + 1), round_value)))

            # sort dataframe values in bins
            second_bin_amount = pd.cut(second_centrality[acronym], bins=bin_edges_extended,
                                       include_lowest=True).value_counts().reset_index()
            second_bin_amount = second_bin_amount.iloc[second_bin_amount['index'].cat.codes.argsort()]

            # create histogram entry
            rects2 = ax.bar(np.array(bin_edges_extended[1:]) + width / 2, second_bin_amount[acronym], width,
                            label=second_scenario + ' scenario', color=second_color, edgecolor='black',
                            linewidth=0.4)
            autolabel(rects2, ax, second_color)

            ax.set_xticks(bin_edges_extended[1:])
            ax.set_xticklabels(label_list_extended)

        else:
            # sort dataframe values in bins
            second_bin_amount = pd.cut(second_centrality[acronym], bins=bin_edges,
                                       include_lowest=True).value_counts().reset_index()
            second_bin_amount = second_bin_amount.iloc[second_bin_amount['index'].cat.codes.argsort()]

            # create histogram entry
            rects2 = ax.bar(np.array(bin_edges[1:]) + width / 2, second_bin_amount[acronym], width,
                            label=second_scenario + ' scenario', color=second_color,
                            edgecolor='black', linewidth=0.4)
            autolabel(rects2, ax, second_color)

            ax.set_xticks(bin_edges[1:])
            ax.set_xticklabels(label_list)

    else:
        ax.set_xticks(bin_edges[1:])
        ax.set_xticklabels(label_list)

    plt.xticks(rotation=90)
    plt.xlabel(axis_label + ' node value')
    plt.ylabel('Amount of nodes')

    ax.legend(loc="upper right")
    plt.tight_layout()

    if second_scenario is None:
        plt.savefig(path.join(DATA_DIR, 'results/plots/' + acronym + '_' + first_scenario + '_hist.png'))
    else:
        plt.savefig(path.join(DATA_DIR, 'results/plots/hist_' + acronym + '.png'))


def cumulative_distribution(acronym, text_x_coord):
    """Create CDF with normal and flooded centrality node values"""
    data_color = SETTINGS['data_color']

    node_data = gpd.read_file(path.join(DATA_DIR, SETTINGS['networks']['normal']))
    node_data2 = gpd.read_file(path.join(DATA_DIR, SETTINGS['networks']['flooded']))

    # sort the data:
    data_sorted = np.sort(node_data[acronym])
    data_sorted2 = np.sort(node_data2[acronym])

    # calculate the proportional values of samples
    p = 1. * np.arange(len(node_data)) / (len(node_data) - 1)
    p2 = 1. * np.arange(len(node_data2)) / (len(node_data2) - 1)

    # plot the sorted data:
    if acronym == 'cls':
        plt.plot(data_sorted, p, label='normal scenario', color=data_color['normal'])
        plt.plot(data_sorted2, p2, label='flooded scenario', color=data_color['flooded'])
        plt.xlabel('HC node value')
    elif acronym == 'btwn':
        plt.plot(data_sorted2, p2, label='flooded scenario', color=data_color['flooded'])
        plt.plot(data_sorted, p, label='normal scenario', color=data_color['normal'])
        plt.xlabel('BC node value')

    plt.ylabel('Relative cumulative share of nodes')
    plt.legend(loc="lower right")

    mean_normal = data_sorted.mean()
    n_normal = len(data_sorted)
    mean_flooded = data_sorted2.mean()
    n_flooded = len(data_sorted2)

    textstr = '\n'.join((
        r'Normal:',
        r' Mean=%.5f' % mean_normal,
        r' N=%d' % n_normal,
        '\n'
        r'Flooded:',
        r' Mean=%.5f' % mean_flooded,
        r' N=%d' % n_flooded
    ))
    props = dict(alpha=0.5, facecolor='white')
    plt.text(text_x_coord, 0.2, textstr, fontsize=10, multialignment='left', bbox=props)

    plt.tight_layout()
    plt.savefig(path.join(DATA_DIR, 'results/plots/cdf_' + acronym + '.png'))


if __name__ == '__main__':

    centrality_name = None
    centrality_acronym = None
    centrality_label = None
    centrality_round_value = None
    plot_folder_path = str(path.join(DATA_DIR, 'results/plots'))

    try:
        centrality_name = str(sys.argv[1])
    except IndexError:
        logging.error('Please provide a centrality name, e.g., Betweenness or Closeness.')
        sys.exit(1)

    # recommendation for jakarta thesis data: 0.0034 for Betweenness and 2.2 for Closeness
    text_x_coordinates = [0.01 if centrality_name == 'Betweenness' else 17][0]

    try:
        text_x_coordinates = float(sys.argv[2])
    except IndexError:
        pass

    if not path.exists(plot_folder_path):
        mkdir(plot_folder_path)

    if centrality_name == 'betweenness' or centrality_name == 'Betweenness':
        centrality_acronym = 'btwn'
        centrality_label = 'BC'
        centrality_round_value = 5
    elif centrality_name == 'closeness' or centrality_name == 'Closeness':
        centrality_acronym = 'cls'
        centrality_label = 'HC'
        centrality_round_value = 3
    else:
        logging.error('Please provide a valid centrality name, e.g., Betweenness or Closeness.')
        sys.exit(1)

    cumulative_distribution(centrality_acronym, text_x_coordinates)
    print('CDF results saved.')

    histogram_centrality(centrality_acronym, centrality_label, centrality_round_value, 'normal', 'flooded')
    print('Histogram results saved.')
