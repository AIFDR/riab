"""IO module for reading and writing of files

   This module provides functionality to read and write
   raster and vector layers from numerical data.
"""

import os
from vector import Vector
from raster import Raster


def read_layer(filename):
    """Read spatial layer from file.
    This can be either coverage or vector data.
    """

    _, ext = os.path.splitext(filename)
    if ext in ['.asc', '.tif']:
        return Raster(filename)
    elif ext in ['.shp', '.gml']:
        return Vector(filename)
    else:
        msg = ('Could not read %s. '
               'Extension %s has not been implemented' % (filename, ext))
        raise Exception(msg)


def write_coverage(A, projection, geotransform, filename):
    """Write array to raster file with specified metadata and one data layer

    Input:
        A: Numpy array containing coverage data
        projection: WKT projection information
        geotransform: 6 digit vector
                      (top left x, w-e pixel resolution, rotation,
                       top left y, rotation, n-s pixel resolution).
                       See e.g. http://www.gdal.org/gdal_tutorial.html
        filename: Output filename


    Note: The only format implemented is GTiff and the extension must be .tif
    """

    R = Raster(A, projection, geotransform)
    R.write_to_file(filename)


def write_point_data(coordinates, projection, attributes, filename):
    """Write coordinates and any associated attributes to vector file

    Input:
        coordinates: Nx2 Numpy array with longitudes, latitudes
                     N is the number of points (features).
        projection: WKT projection information
        attributes: List of N dictionaries each with M fields where
                    M is the number of attributes.
                    A value of None is acceptable.
        filename: Output filename


    Note: The only format implemented is GML and SHP so the extension
    must be either .gml or .shp

    # FIXME (Ole): When the GML driver is used,
    #              the spatial reference is not stored.
    #              I suspect this is a bug in OGR.

    Background:
    * http://www.gdal.org/ogr/ogr_apitut.html (last example)
    * http://invisibleroads.com/tutorials/gdal-shapefile-points-save.html
    """

    V = Vector(coordinates, projection, attributes)
    V.write_to_file(filename)
