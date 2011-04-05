
#FIXME (Ole): Merge this into io.py

"""
Python library to upload and download data from GeoNode
"""
import os
import urllib
import urllib2
import httplib2
import time
import contextlib
from utilities import MultipartPostHandler
import datetime
from xml.etree.ElementTree import parse
from StringIO import StringIO
import tempfile
from zipfile import ZipFile
from owslib.wfs import WebFeatureService
from owslib.wcs import WebCoverageService
from django.conf import settings
from riab_server.core.io import read_layer
from riab_server.core.utilities import get_layers_metadata

WCS_TEMPLATE = '%s?version=1.0.0' + \
                      '&service=wcs&request=getcoverage&format=GeoTIFF&' + \
                      'store=false&coverage=%s&crs=EPSG:4326&bbox=%s' + \
                      '&resx=0.030741064&resy=0.030741064'

WFS_TEMPLATE = '%s?service=WFS&version=1.0.0' + \
               '&request=GetFeature&typeName=%s&maxFeatures=500' + \
               '&outputFormat=SHAPE-ZIP&bbox=%s'


def metadata(server_url, layer_name):
    """Uses OWS services to determine if the data is raster or vector
    """
    themetadata = get_layers_metadata(server_url, version='1.0.0')

    stuff = [x[1] for x in themetadata if x[0] == layer_name]
    if len(stuff) == 0:
        if ':' in layer_name:
            name = layer_name.split(':')[1]
            stuff = [x[1] for x in themetadata if x[0] == name]

            if len(stuff) == 0:
                return None
        else:
            return None

    assert len(stuff) > 0
    layer_metadata = stuff[0]
    assert layer_metadata is not None
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

       Data_type can be either 'vector' or 'raster'
    """
    template = None
    layer_metadata = metadata(server_url, layer_name)
    data_type = layer_metadata['layerType']
    if data_type == 'feature':
        template = WFS_TEMPLATE
        suffix = '.zip'
        download_url = template % (server_url, layer_name, bbox)
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
        download_url = template % (server_url, layer_name, bbox)
        filename = get_file(download_url, suffix)
    lyr = read_layer(filename)
    #FIXME (Ariel) Don't monkeypatch the layer object
    lyr.metadata = layer_metadata
    return lyr


def dummy_save(filename, title, user, metadata=''):
    """Take a file-like object and uploads it to a GeoNode
    """
    return 'http://dummy/data/geonode:' + filename + '_by_' + user.username
