"""Utilities for impact.storage
"""

import numpy
from osgeo import ogr, gdal
from tempfile import mkstemp

# The projection string depends on the gdal version
DEFAULT_PROJECTION = '+proj=longlat +datum=WGS84 +no_defs'

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


# Miscellaneous auxiliary functions
def unique_filename(suffix=None):
    """Create new filename guarenteed not to exist previoously

    Use mkstemp to create the file, then remove it and return the name
    """

    _, filename = mkstemp(suffix=suffix)

    try:
        os.remove(filename)
    except:
        pass

    return filename

