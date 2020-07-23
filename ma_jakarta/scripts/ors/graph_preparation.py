# -*- coding: utf-8 -*-
from __init__ import BASEDIR, NETWORK_DIR
import subprocess
from os import path, mkdir
import shutil
import sys
import logging


class ORSGraphPrep:
    """Convert network graph format from .shp to .osm.pbf"""

    def __init__(self, graph_name):
        self.graph_name = graph_name
        self.osmconvert = path.join(BASEDIR, 'ma_jakarta/scripts/osmconvert')
        self.edge_shp_file = path.join(NETWORK_DIR, graph_name + '/edges.shp')
        self.osm_file = path.join(BASEDIR, 'ma_jakarta/openrouteservice/docker/data/preprocess/' + graph_name + '.osm')
        self.osm_modified_file = path.join(BASEDIR,
                                      'ma_jakarta/openrouteservice/docker/data/preprocess/' + graph_name + '_modified.osm')
        self.osmpbf_file = path.join(BASEDIR, 'ma_jakarta/openrouteservice/docker/data/' + graph_name + '.osm.pbf')

    def convert_shp2osm(self):  # network_edge_shp_file, preprocessed_osm_file
        """convert edge .shp to .osm file"""
        cmd_shp_osm = 'ogr2osm ' + self.edge_shp_file + ' -o ' + self.osm_file
        proc_osm = subprocess.Popen(cmd_shp_osm,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    shell=True)
        return_code_osm = proc_osm.wait()
        if return_code_osm:
            raise subprocess.CalledProcessError(return_code_osm, cmd_shp_osm)
        print('Converted .shp to .osm')

    def convert_neg2pos_values(self):
        """Modify negative OpenStreetMap ids and refs to positive values. Needed to build openrouteservice graph."""
        with open(self.osm_file, 'r') as inputfile:
            with open(self.osm_modified_file, 'w') as outputfile:
                filedata = inputfile.read()
                # Replace negative values by positive values
                filedata = filedata.replace('id="-', 'id="')
                filedata = filedata.replace('nd ref="-', 'nd ref="')
                outputfile.write(filedata)
        print('Modified negative ids and refs to positive values.')

    def convert_osm2osmpbf(self):
        """Convert .osm file to .osm.pbf file"""
        cmd_osm_osmpbf = self.osmconvert + ' ' + self.osm_modified_file + ' -o=' + self.osmpbf_file
        proc_osmpbf = subprocess.Popen(cmd_osm_osmpbf,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       shell=True)
        return_code_osmpbf = proc_osmpbf.wait()
        if return_code_osmpbf:
            raise subprocess.CalledProcessError(return_code_osmpbf, cmd_osm_osmpbf)
        print('Converted .osm to .osm.pbf')

    def convert(self):
        mkdir(path.join(BASEDIR, 'ma_jakarta/openrouteservice/docker/data', 'preprocess'))
        self.convert_shp2osm()
        self.convert_neg2pos_values()
        self.convert_osm2osmpbf()
        shutil.rmtree(path.join(BASEDIR, 'ma_jakarta/openrouteservice/docker/data/preprocess'), ignore_errors=True)


if __name__ == '__main__':
    network_graph_name = None

    try:
        network_graph_name = str(sys.argv[1])
    except IndexError:
        logging.error('Please provide an existing network graph name.')

    if not path.exists(path.join(BASEDIR, 'ma_jakarta/openrouteservice/docker/data', network_graph_name + '.osm.pbf')):
        ORSGraphPrep(network_graph_name).convert()
    else:
        print(network_graph_name + '.osm.pbf already exists.')

    # adjust docker-compose.yml: OSM_FILE and volumes
    # make sure there exists no docker/graph folder.
    # If rename to e.g. graphs_floodprone to keep data. ORS builds graph from "graphs" folder
    # in folder openrouteservice/docker: docker-compose up -d
