# -*- coding: utf-8 -*-
from __init__ import SETTINGS
import numpy as np
from matplotlib import ticker


def autolabel(rects, ax):
    for rect in rects:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2., 1 * h, '%d' % round((h * 1e-6)),
                ha='center', va='bottom', rotation='vertical')


def create_histogram(city_area_size, df, amenity_type, ax, y_label, title, y_rounding):
    """Create histogram for reached/accessed area and population"""
    bar_color = SETTINGS['bar_color']
    amenity_data = []
    ind = np.arange(6)
    width = 0.3
    rects = []

    for scenario in df:
        amenity_data.append(list(df[scenario][amenity_type].values()))

    x_labels = ['0 - <=5', '>5 - <=10', '>10 - <=15', '>15 - <=20', '>20 - <=25', '>25 - <=30']

    rects.append([ax.bar(ind - width/2, amenity_data[0], width, color=bar_color[0], edgecolor='black')])
    rects.append([ax.bar(ind + width/2, amenity_data[1], width, color=bar_color[1], edgecolor='black')])
    rects.append([ax.axhline(y=city_area_size, color='#2eb82e', linestyle='-')])

    ax.set_ylabel(y_label)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, p: '%d' % (y * y_rounding)))

    ax.set_xticks(ind)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel('Time range [min]')
    ax.legend((rect[0] for rect in rects), ('Normal', 'Flooded', 'Total city ' + title + ' size'), loc="lower right")
    ax.set_title('Reached ' + title + ' for health amenity type ' + str(amenity_type))
