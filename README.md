# Flood Impact Assessment on Road Network and Healthcare Access

This application was developed for the thesis, provided in `MA_Klipper.pdf`.

Successful access to healthcare depends, inter alia, on the existence of health locations with the specific care capacities. Furthermore, the available road network is important for the mobility-based accessibility, to actually reach the health site. This application can be used to analyse the road network and the accessibility to healthcare. Within the paper, the case scenario of Jakarta, Indonesia was examined, based on [OpenStreetMap](https://www.openstreetmap.org/about) and [HOT Indonesia](https://openstreetmap.id/en/) provided data. With the exception of flood data, all data and tools are open source and free of charge and can be downloaded for any location worldwide.

## Installation

- Clone git repository: `git clone https://github.com/GIScience/Jakarta_Thesis_Klipper.git`

- `cd Jakarta_Thesis_Klipper`

### [Conda](https://docs.conda.io/en/latest/)

- Install e.g. [miniconda3](https://docs.conda.io/en/latest/miniconda.html)

- Create virtual environment `conda create --name jakarta_venv python=3.7`

- Activate environment `conda activate jakarta_venv`

### [Poetry](https://python-poetry.org/docs/)

- Install poetry, e.g.:

`curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python`

- To activate poetry command, run the following command: `source $HOME/.poetry/env`

- To install the for the application needed python packages, run: `poetry install`

- To additionally install GDAL properly, run:

`pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal" `


### [Docker](https://pypi.org/project/docker/) 

- Install docker, eg: `pip install docker`


## Input data

The input data must be provided by the user. Please save the data in `ma_jakarta/data/input`. You can set the files names in `settings.yml`. Example data for the area of Heidelberg is provided, which you can use for testing.

- `city border`: get it for instance from [overpass-turbo](https://overpass-turbo.eu/)

- `healthsite amenities`: get it for instance from [overpass-turbo](https://overpass-turbo.eu/)

- `flood data`

- `populaiton raster`: get it for instance from here: https://data.humdata.org/ 


## Run

### 1. Data preprocessing
To preprocess data run one of the following commands once. 

- If you are using OSM data, downloaded from [overpass-turbo](https://overpass-turbo.eu/), run: 

`python ma_jakarta/scripts/data_preprocessing/run_preprocessing.py`.

- If you are using HOT provided amenity [data](https://drive.google.com/drive/folders/1azUAetAfVKHmkh8MdBnZv6owD-jzvBkd)
run: 

`python ma_jakarta/scripts/data_preprocessing/run_preprocessing.py HOT`.


### 2. Road network

#### 2.1. Download and preperation of network graph

- To download network data, run either:

`python ma_jakarta/scripts/network/download_network.py 'hd_border.shp' 'drive_service' 'normal' 'ma_jakarta/network_graphs'` 

to download data for user provided `city_border.shp`, defined in `settings.yml` 
(read more about it here: https://osmnx.readthedocs.io/en/stable/osmnx.html#osmnx.core.graph_from_polygon)

- or:

`python ma_jakarta/scripts/network/download_network.py 'Jakarta, Indonesia' 'drive_service' 'normal' 'ma_jakarta/network_graphs'`

(read more about it here: https://osmnx.readthedocs.io/en/stable/osmnx.html#osmnx.core.graph_from_place)

where:

   `hd_border.shp` or `Jakarta, Indonesia`  defines the spatial area for the network data to download

   change `drive_service` to e.g. `walk`, `bike`, `drive`, `all`, `all_private` to change the type of the street network

   `normal`: the graph's folder name -> keep this name for the normal scenario and for following calculations 

   `ma_jakarta/network_graphs`: the output's folder path 


#### 2.2. Network centrality (and creation of flood related network)

- To calculate graph centrality, run:

`python ma_jakarta/scripts/network/run_network.py scenario first_centrality [second_centrality]`

if a flood related scenario is given, the network will be first intersected with the flood layer and saved separately

where: 

   `scenario`: scenario name, e.g., `normal` or `flooded` -> `normal`: network graph folder name with parent folder `ma_jakarta/network_graphs`

   `first_centrality`: centrality name, e.g., `Betweenness` and `Closeness`

   `[second_centrality]`: optional second centrality name, e.g., `Betweenness` and `Closeness`


Note: 

- The network graph and each edge is weighted with the minimum needed and allowed car driving duration to receive insights about the fastest driving behavior.
- Betweenness Centrality (BC): Based on shortest path calculation between two nodes, will be applied on every available node combination. Can be used to identify the freqency of each crossed road junction, based on car driving, fastest routing profile on all possible routes within the city. Road segments with a high BC value are important for fast and efficient traffic, but can pose the danger of congestion.
- (Harmonic) Closeness Centrality (HC/CC): Based on shortest path calculation between two nodes, will be applied on every available node combination. Can be used to identify the locations within the city that are the fastest on average to be accessed. Those locations can be used as good supply points within the city.

#### 2.3. Network resilience 

- For empirical value distribution as CDF and histogram, run: 

`python ma_jakarta/scripts/analysis/network_resilience/emp_value_distribution.py centrality`

where:
 
   `centrality`: centrality name, e.g., `Betweenness` and `Closeness`

- For flood impact on network centrality, run: 

`python ma_jakarta/scripts/analysis/network_resilience/node_difference.py first_centrality [second_centrality]`

where: 

   `first_centrality`: centrality name, e.g., `Betweenness` and `Closeness`

   `[second_centrality]`: optional second centrality name, e.g., `Betweenness` and `Closeness`

- For small and large foreground network as well as sameness ratio, run: 

`python ma_jakarta/scripts/analysis/network_resilience/resilience.py centrality`

where:
 
   `centrality`: centrality name, e.g., `Betweenness` or `Closeness`


### 3. Healthcare access

#### 3.1. Healthcare supply

- To receive results regarding the spatial distribution of health locations and bed capacity, run: 

`python ma_jakarta/scripts/analysis/health_distribution.py scenario first_analysis_choice [second_analysis_choice]`

where:
 
   `scenario`: scenario name, e.g., `normal` or `flooded` 

   `first_analysis_choice`: define the desired analysis calculation type, e.g., `health_location` or `bed_capacity`

   `[second_analysis_choice]`: define optional second analysis calculation type, e.g., `health_location` or `bed_capacity`
   
   `health_location`: the spatial distribution of available health sites

   `bed_capacity`: the spatial distribution of available health beds -> This option is only available if respective data for each 
   health site is provided. If this is the case, please make sure, that the data column is named `cap_int` for the amount 
   of available capacity.


#### 3.2. Mobility-based accessibility

##### Install openrouteservice

- `cd ma_jakarta`

- `git clone https://github.com/GIScience/openrouteservice.git`

- `cd openrouteservice`

- `git checkout development`

- `cd ../../`

- `mv ma_jakarta/app.config.sample ma_jakarta/openrouteservice/docker/app.config.sample`

##### Build local openrouteservice instance

- To create the for the routing graph needed OSM file based on the network graph data, run:  

`python ma_jakarta/scripts/isochrone/graph_preparation.py scenario`

where: 

`scenario`: scenario name, e.g., `normal` or `flooded`

- A few more steps to create the routing graph: 

    - adjust `openrouteservice/docker/docker-compose.yml`: use the just created file 
(located in `openrouteservice/docker/data/`) to change osm file in `OSM_FILE` and `volumes` -> e.g. 
`OSM_FILE: ./docker/data/heidelberg.osm.gz` to `OSM_FILE: ./docker/data/normal.osm.pbf`

   - make sure there is no `docker/graph` folder existing. If, rename to, e.g., `graphs_normal` to keep data. Openrouteservice builds graph from `graphs` folder. 
To rename graph, run: 

`mv ma_jakarta/openrouteservice/docker/graphs ma_jakarta/openrouteservice/docker/graphs_normal`

    - `cd ma_jakarta/openrouteservice/docker`

   - To build openrouteservice graph, run:
    
`docker-compose up -d`

It takes a bit to build the graph, even if the script has finished successfully. The graph is built when the `graphs` folder includes 
the subgraphs `vehicles-car` and `vehicles-hgv`, which include files like `edges`, `geometry`, `location_index`.  
(If graph is not created properly, run: `docker-compose up -d --build`)

Note: If your are not changing the routing graph to the flooded scenario, you will request the isochrones on the 
normal scenario, which means you will use the reduced number of not flooded health locations but on all streets within the city.
However, during the flood scenario, some streets are flooded and consequently not passable.  

##### Request isochrones

First register for free for a valid [openrouteservice](https://openrouteservice.org/dev/#/signup) API key and provide it in `settings.yml` > `ors_api_key`.

Define the isochrone time ranges in `settings.yml` > `iso_range_values`, default: `iso_range_values: [300, 600, 900, 1200, 1500, 1800]`. 
The time values are defined in seconds.  

- To request the isochrones, run: 

`python ma_jakarta/scripts/isochrone/isochrone.py scenario`

where: 

   `scenario`: scenario name, e.g., `normal` or `flooded` 

Note: For the flooded scenario two output files will be created: `pre_flooded` -> only the isochorones and
`flooded` -> flooded areas within isochrones, which were created due to simplification,
and data outside the city border are removed. The `pre_flooded` is needed for the subsequent analysis step. 
The flooded areas as well as the data spatially outside the city will be removed within the next steps. 


##### Impact access maps and histogram

Define the health amenity types in `settings.yml` > `amenity_osm_values` for which you want to receive an output. 
Default: `amenity_osm_values: ['hospital','clinic']`

- To execute the calculation, run: 

`python ma_jakarta/scripts/analysis/impact_mobility_access/run_analysis.py first_analysis_choice [second_analysis_choice]`

where:

   `first_analysis_choice`: define the desired analysis calculation type, e.g., `impact_maps` or `histogram`

   `[second_analysis_choice]`: define optional second analysis calculation type, e.g., `impact_maps` or `histogram`

   `impact_maps`: flood impact on isochrones and accessed areas with health locations as centre. 
   The spatial difference of each isochrone between the flooded and the normal scenario will be calculated.

   `histogram`: accessed area size and amount of population with access to health locations 
   for the normal and the flooded scenario will be visualised in a histogram


#### 3.3. Supply and demand related access

- To execute the analysis, run:
 
`python ma_jakarta/scripts/analysis/supply_demand.py analysis scenario amenity_type time_range`

where: 

   `analysis` implements the analysis calculation 

   `scenario`: scenario name, e.g., `normal` or `flooded` -> for further analysis step run first for normal and second for flooded scenario

   `amenity_type`: the health location type -> default `hospital`

   `time_range`: the isochrone duration value -> default `300` -> a small value is recommended since differences 
   in local accessibility can be better identified on a small scale

- To get insights about the data, run:

`python ma_jakarta/scripts/analysis/supply_demand.py stats column_name percentile_value`

where: 

   `stats` implements the analysis step

   `column_name`: the column you want to get insights about, e.g., `pop_area`

   `percentile_value`, e.g., 95: get the 95th percentile


### This API was tested:

- on a Manjaro Linux 

- Python 3.7

- Conda environment: version 4.8.2

- Poetry version 1.0.5

- docker version 19.03.6-ce, build 369ce74a3c
