# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker


def autolabel(rects, ax):
    for rect in rects:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2., 1 * h, '%d' % round((h * 1e-6)),
                ha='center', va='bottom', rotation='vertical')


def create_histogram(df, amenity_type, ax, y_label, title, y_rounding):
    """"""
    hosp_data = []
    x_label = None
    ind = np.arange(6)
    width = 0.3
    rects = []
    counter = 0

    for scenario in df:
        hosp_data.append(list(df[scenario][amenity_type].values()))
        x_label = list(df[scenario][amenity_type].keys())

    for hosp in range(len(hosp_data)):
        rect = ax.bar(ind + counter * width, hosp_data[counter], width)
        rects.append([rect])
        counter += 1

    ax.set_ylabel(y_label)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: '%d' % (y * y_rounding)))
    ax.set_xlabel('Time range [min]')
    ax.set_xticks(ind + width)
    ax.set_xticklabels([int(label / 60) for label in x_label])
    ax.legend((rect[0] for rect in rects), ([scenario for scenario in df]))
    #     ax.set_title('Reached ' + title + ' for health amenity type ' + str(amenity_type))
    ax.set_title(title + ' for health amenity type ' + str(amenity_type))

    # for rect in rects:
    #     autolabel(rect[0], ax)


def create_table(df, output_path):
    fig, ax = plt.subplots()

    # hide axes
    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    ax.table(cellText=df.values, colLabels=df.columns, loc='center')

    # fig.tight_layout()

    # plt.savefig(output_path)
