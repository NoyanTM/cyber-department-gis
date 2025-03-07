# pipeline

## Installation
- [gdal (gis toolkit)](https://github.com/OSGeo/gdal):
  - 1. from repository:
    - sudo apt-add-repository ppa:ubuntugis/ubuntugis-stable
    - sudo apt install -y gcc g++
    - sudo apt install -y libgdal-dev gdal-bin python3-gdal
    - export CPLUS_INCLUDE_PATH=/usr/include/gdal; export C_INCLUDE_PATH=/usr/include/gdal; or export CFLAGS=$(gdal-config --cflags)
    - uv add wheel
    - uv add gdal==$(gdal-config --version); or pip install --global-option=build_ext --global-option="-I/usr/include/gdal"
  - 2. pre-builded wheels:
    - https://github.com/cgohlke/geospatial-wheels
    - uv install gdal_version.whl
  - 3. testing if installed:
    - python3 -c 'from osgeo import gdal; print(gdal.VersionInfo("–version"))'
- [uv (environment)](https://github.com/astral-sh/uv):
  - uv venv
  - uv install
  - source .venv/bin/activate
- [sam2 (pre-trained model)](https://github.com/facebookresearch/sam2):
  - 
