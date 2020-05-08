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


## run

### data preprocesesing

#### 1. data preprocessing
run once to preprocess data: `python ma_jakarta/scripts/data_preprocessing/run_preprocessing.py`


### network

#### 2. network data 
run once to download network data, either:

`python ma_jakarta/scripts/network/download_network.py 'hd_border.shp' 'drive' 'normal' 'ma_jakarta/network_graphs'` 
to download data for city_border shapefile, defined in settings.yml, or: 

`python ma_jakarta/scripts/network/download_network.py 'Jakarta, Indonesia' 'drive' 'normal' 'ma_jakarta/network_graphs'`

- where `Jakarta, Indonesia`  defines the data for the desired place

- change `drive` to e.g. `walk`, `bike`, `drive_service`, `all`, `all_private` to change the type of the street network

- `normal`: the graph's folder name

- `ma_jakarta/network_graphs`: the output's folder path 

https://osmnx.readthedocs.io/en/stable/osmnx.html#osmnx.core.graph_from_polygon

https://osmnx.readthedocs.io/en/stable/osmnx.html#osmnx.core.graph_from_place

#### 3. flood network and centrality

run to calculate centrality `python ma_jakarta/scripts/network/run_network.py normal Betweenness Closeness`
if a flood related scenario is given the network will be first intersected with the flood layer and saved separately e.g. 
`python ma_jakarta/scripts/network/run_network.py floodprone Betweenness Harmonic_Closeness`

- where `normal`: network graph folder name with parent folder `ma_jakarta/network_graphs`

- `Betweenness Closeness`: Centrality declaration, choose one or both  


### ors

#### install ors

- `cd ma_jakarta`

- `git clone https://github.com/GIScience/openrouteservice.git`

- `cd openrouteservice`

- `git checkout development`

- `cd ../../`

- `sudo mv ma_jakarta/app.config.sample ma_jakarta/openrouteservice/docker/app.config.sample`

#### 4. build ors graph 

- `python ma_jakarta/scripts/ors/graph_preparation.py floodprone`

- adjust docker-compose.yml: OSM_FILE and volumes

- make sure there is no `docker/graph` folder existing. If rename to e.g. graphs_floodprone to keep data. ORS builds graph from "graphs" folder. 
To rename graph: `sudo mv ma_jakarta/openrouteservice/docker/graphs ma_jakarta/openrouteservice/docker/graphs_floodprone`

- `cd ma_jakarta/openrouteservice/docker`

- `docker-compose up -d`

It takes a bit to build the graph, even if the script has finished successfully. The graph is built when the `grpahs` folder includes 
the subgraphs `vehicles-car` and `vehicles-hgv`, which include files like `edges`, `geometry`, `location_index`.  
(`docker-compose up -d --build`)

#### 5. isochrones

- run `python ma_jakarta/scripts/ors/isochrone.py your-ors-api-key floodprone`

### analysis

#### 6. access analysis

- run `python ma_jakarta/scripts/analysis/run_analysis.py histogram impact_maps`

#### 7. node centrality change

- run `python ma_jakarta/scripts/analysis/node_difference.py floodprone Betweenness Closeness`

