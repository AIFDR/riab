"""Utilities for impact.storage
"""

import numpy
from osgeo import ogr, gdal

# Map between extensions and ORG drivers
driver_map = {'.shp': 'ESRI Shapefile',
              '.gml': 'GML',
              '.tif': 'GTiff'}

# Map between Python types and OGR field types
# FIXME (Ole): I can't find a double precision type for OGR
type_map = {type(''): ogr.OFTString,
            type(0): ogr.OFTInteger,
            type(0.0): ogr.OFTReal,
            type(numpy.array([0.0])[0]): ogr.OFTReal,  # numpy.float64
            type(numpy.array([[0.0]])[0]): ogr.OFTReal}  # numpy.ndarray
