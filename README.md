# Working process!


## Installation

- `git clone https://gitlab.com/isikl/ma.git`

- `cd ma`

## install poetry: https://python-poetry.org/docs/
- `curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python`

- To activate poetry command, run the following command: `source $HOME/.poetry/env`

- `poetry install`


## install docker 


### This API was tested:

- on a Manjaro Linux 

- Conda environment: version 4.8.2

- Poetry version 1.0.5

- docker version 19.03.6-ce, build 369ce74a3c



#### error handeling
https://rasterio.readthedocs.io/en/latest/faq.html

ERROR 4: Unable to open EPSG support file gcs.csv.  Try setting the GDAL_DATA environment variable to point to the directory containing EPSG csv files.
ERROR:fiona._env:Unable to open EPSG support file gcs.csv.  Try setting the GDAL_DATA environment variable to point to the directory containing EPSG csv files.

GDAL_DATA="/home/isabell/Workspace/test/ma/ma-jakarta/data/idn_ppp_2020.tif" 


### file declaration
- complete/normal/daily scenario graph must be named `normal`

- for further graph scenarios: make sure the graph holds the same name as the preprocessed intersection flood file in `settings.yml`, 
e.g. `floodprone`: graph name: `network_graphs/floodprone` and flood layer: `floodprone: 'preprocessed/floodprone.shp'`


### run

#### data preprocessing
run once to preprocess data: `python ma_jakarta/scripts/data_preprocessing/run_preprocessing.py`


#### network data 
run once to download network data `python ma_jakarta/scripts/network/download_network.py 'Jakarta, Indonesia' 'drive' 'normal' 'ma_jakarta/network_graphs'`

- where `Jakarta, Indonesia`  defines the data for the desired place

- change `drive` to e.g. `walk`, `bike`, `drive_service`, `all`, `all_private` to change the type of the street network

- `normal`: the graph's folder name

- `ma_jakarta/network_graphs`: the output's folder path 

https://osmnx.readthedocs.io/en/stable/osmnx.html#osmnx.core.graph_from_place

##### network centrality

run to calculate centrality `python ma_jakarta/scripts/network/run_network.py normal Betweenness Harmonic_Closeness`

- where `normal`: network graph folder name with parent folder `ma_jakarta/network_graphs`

- `Betweenness Harmonic_Closeness`: Centrality declaration, choose one or both  


#### ors

##### install ors and build

- `cd ma_jakarta`

- `git clone https://github.com/GIScience/openrouteservice.git`

- `cd openrouteservice`

- `git checkout development`

- `cd ../`

- `python ma_jakarta/scripts/ors/graph_preparation.py floodprone`

- `sudo mv ma_jakarta/app.config.sample ma_jakarta/openrouteservice/docker/app.config.sample`

- adjust docker-compose.yml: OSM_FILE and volumes

- make sure there is no `docker/graph` folder existing. If rename to e.g. graphs_floodprone to keep data. ORS builds graph from "graphs" folder. 
To rename graph: `sudo mv ma_jakarta/openrouteservice/docker/graphs ma_jakarta/openrouteservice/docker/graphs_floodprone`

- in folder openrouteservice/docker: `docker-compose up -d`

It takes a bit to build the graph, even if the script has finished successfully. The graph is built when the `grpahs` folder includes 
the subgraphs `bike`, `pedestrian-walk`, `vehicles-car`, `vehicles-hgv`, which include files like `edges`, `geometry`, `location_index`.  

##### isochrones

- run `python ma_jakarta/scripts/ors/isochrone.py your-ors-api-key floodprone`


### TODO: 

- use own ors fork? -> adjust maximum_snapping_radius: 350m is too large..
