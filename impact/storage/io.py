"""IO module for reading and writing of files

   This module provides functionality to read and write
   raster and vector layers from numerical data.
"""

import os
import urllib2
import time
import contextlib
import tempfile
from zipfile import ZipFile

from impact.storage.vector import Vector
from impact.storage.raster import Raster
from impact.storage.utilities import get_layers_metadata


def read_layer(filename):
    """Read spatial layer from file.
    This can be either raster or vector data.
    """

    _, ext = os.path.splitext(filename)
    if ext in ['.asc', '.tif']:
        return Raster(filename)
    elif ext in ['.shp', '.gml']:
        return Vector(filename)
    else:
        msg = ('Could not read %s. '
               'Extension "%s" has not been implemented' % (filename, ext))
        raise Exception(msg)


def write_raster_data(data, projection, geotransform, filename):
    """Write array to raster file with specified metadata and one data layer

    Input:
        data: Numpy array containing grid data
        projection: WKT projection information
        geotransform: 6 digit vector
                      (top left x, w-e pixel resolution, rotation,
                       top left y, rotation, n-s pixel resolution).
                       See e.g. http://www.gdal.org/gdal_tutorial.html
        filename: Output filename

    Note: The only format implemented is GTiff and the extension must be .tif
    """

    R = Raster(data, projection, geotransform)
    R.write_to_file(filename)


def write_point_data(data, projection, geometry, filename):
    """Write point data and any associated attributes to vector file

    Input:
        data: List of N dictionaries each with M fields where
              M is the number of attributes.
              A value of None is acceptable.
        projection: WKT projection information
        geometry: Nx2 Numpy array with longitudes, latitudes
                  N is the number of points (features).
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

    V = Vector(data, projection, geometry)
    V.write_to_file(filename)

# FIXME (Ole): Why is the resolution hard coded here?
WCS_TEMPLATE = '%s?version=1.0.0' + \
                      '&service=wcs&request=getcoverage&format=GeoTIFF&' + \
                      'store=false&coverage=%s&crs=EPSG:4326&bbox=%s' + \
                      '&resx=0.005&resy=0.005'

# FIXME (Ole): Why is maxFeatures hard coded?
WFS_TEMPLATE = '%s?service=WFS&version=1.0.0' + \
               '&request=GetFeature&typeName=%s&maxFeatures=500' + \
               '&outputFormat=SHAPE-ZIP&bbox=%s'


def get_bounding_box(filename):
    """Get bounding box for specified raster or vector file
    """
    layer = read_layer(filename)
    return layer.get_bounding_box()


def get_metadata(server_url, layer_name):
    """Uses OWS services to get the metadata for a given layer
    """
    #FIXME: Make sure server_url is an actual url
    themetadata = get_layers_metadata(server_url, version='1.0.0')

    layer_metadata = None
    for x in themetadata:
        # This is taking care of differences between wcs and wfs layers
        # wfs has a preceding workspace but wcs does not.
        if ':' in x[0]:
            x_layer_name = x[0].split(':')[1]
        else:
            x_layer_name = x[0]

        if ':' in layer_name:
            plain_layer_name = layer_name.split(':')[1]
        else:
            plain_layer_name = layer_name

        if x_layer_name == layer_name:
            # We expect only one element in this list, if there is more
            # than one, we will use the first one.
            layer_metadata = x[1]
            break

    msg = 'There is no metadata in server %s for layer %s' % (server_url, layer_name)
    assert layer_metadata is not None, msg

    # FIXME: We need a geotransform attribute in get_metadata
    # Let's add it here for the time being

    return layer_metadata


def get_file(download_url, suffix):
    """Download a file from an HTTP server.
    """

    tempdir = '/tmp/%s' % str(time.time())
    os.mkdir(tempdir)
    t = tempfile.NamedTemporaryFile(delete=False,
                                    suffix=suffix,
                                    dir=tempdir)
    with contextlib.closing(urllib2.urlopen(download_url)) as f:
        t.write(f.read())

    filename = os.path.abspath(t.name)
    return filename


def download(server_url, layer_name, bbox):
    """Download the source data of a given layer.

       Input
           server_url: String such as 'http://www.aifdr.org:8080/geoserver/ows'
           layer_name: String such as 'geonode:Earthquake_Ground_Shaking'
           bbox: Bounding box for layer. This can either be a string or a list
                 with format [west, south, east, north], e.g.
                 '87.998242,-8.269822,117.046094,5.097895'


       Layer type can be either 'vector' or 'raster'
    """

    # Input checks
    assert isinstance(server_url, basestring)

    assert isinstance(layer_name, basestring)

    if isinstance(bbox, list):
        assert len(bbox) == 4
        bbox_string = '%f,%f,%f,%f' % tuple(bbox)
    elif isinstance(bbox, basestring):
        bbox_string = bbox
    else:
        msg = ('Bounding box must be a string or a list of coordinates with '
               'format [west, south, east, north]. I got %s' % bbox)
        raise Exception(msg)

    # Create REST request and download file
    template = None
    layer_metadata = get_metadata(server_url, layer_name)

    data_type = layer_metadata['layer_type']
    if data_type == 'feature':
        template = WFS_TEMPLATE
        suffix = '.zip'
        download_url = template % (server_url, layer_name, bbox_string)
        thefilename = get_file(download_url, suffix)
        dirname = os.path.dirname(thefilename)
        t = open(thefilename, 'r')
        zf = ZipFile(t)
        namelist = zf.namelist()
        zf.extractall(path=dirname)
        (shpname,) = [name for name in namelist if '.shp' in name]
        filename = os.path.join(dirname, shpname)
    elif data_type == 'raster':
        template = WCS_TEMPLATE
        suffix = '.tif'
        download_url = template % (server_url, layer_name, bbox_string)
        filename = get_file(download_url, suffix)

    # Instantiate layer from file
    lyr = read_layer(filename)

    #FIXME (Ariel) Don't monkeypatch the layer object
    lyr.metadata = layer_metadata
    return lyr


def dummy_save(filename, title, user, metadata=''):
    """Take a file-like object and uploads it to a GeoNode
    """
    return 'http://dummy/data/geonode:' + filename + '_by_' + user.username
