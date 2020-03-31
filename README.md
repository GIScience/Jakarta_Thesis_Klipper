## Installation

- `git clone https://gitlab.com/isikl/ma.git`

- `cd ma`

# install poetry: https://python-poetry.org/docs/
- `curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python`

- To activate poetry command, run the following command: `source $HOME/.poetry/env`

- `poetry install`


# install docker 


# install and run ors
- `cd ma-jakarta`

- `git clone https://github.com/GIScience/openrouteservice.git `

- `cd openrouteservice`

- `git checkout development`

- `mkdir docker/data/preprocess`

- adjust filename in ors_graph_build.py and run

- adjust docker-compose.yml: OSM_FILE and volumes

- make sure there is no docker/graph folder existing. If rename to e.g. graphs_floodprone to keep data. ORS builds raph from "graphs" folder

- in folder ma/openrouteservice/docker: `docker-compose up -d`


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

