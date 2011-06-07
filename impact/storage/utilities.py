"""Utilities for impact.storage
"""

import os
import numpy
from osgeo import ogr, gdal
from tempfile import mkstemp
import cgi
from urllib import urlencode
from urllib2 import urlopen
from owslib.etree import etree

# The projection string depends on the gdal version
DEFAULT_PROJECTION = '+proj=longlat +datum=WGS84 +no_defs'

# Spatial layer file extensions that are recognised in Risiko
# FIXME: Perhaps add '.gml', '.zip', ...
LAYER_TYPES = ['.shp', '.asc', '.tif', '.tiff', '.geotif', '.geotiff']

# Map between extensions and ORG drivers
DRIVER_MAP = {'.shp': 'ESRI Shapefile',
              '.gml': 'GML',
              '.tif': 'GTiff',
              '.asc': 'AAIGrid'}

# Map between Python types and OGR field types
# FIXME (Ole): I can't find a double precision type for OGR
TYPE_MAP = {type(''): ogr.OFTString,
            type(0): ogr.OFTInteger,
            type(0.0): ogr.OFTReal,
            type(numpy.array([0.0])[0]): ogr.OFTReal,  # numpy.float64
            type(numpy.array([[0.0]])[0]): ogr.OFTReal}  # numpy.ndarray


# Miscellaneous auxiliary functions
def unique_filename(**kwargs):
    """Create new filename guarenteed not to exist previoously

    Use mkstemp to create the file, then remove it and return the name

    See http://docs.python.org/library/tempfile.html for details.
    """

    _, filename = mkstemp(**kwargs)

    try:
        os.remove(filename)
    except:
        pass

    return filename


# GeoServer utility functions
def is_server_reachable(url):
    """Make an http connection to url to see if it is accesible.

       Returns boolean
    """
    try:
        urlopen(url)
    except Exception:
        return False
    else:
        return True


def get_layers_metadata(url, version='1.0.0'):
    """Return the metadata for each layer as an dict formed from the keywords

    The keywords are parsed and added to the metadata dictionary
    if they conform to the format "identifier:value".

    default searches both feature and raster layers by default
      Input
        url: The wfs url
        version: The version of the wfs xml expected

      Returns
        A list of dictionaries containing the metadata for each layer
    """

    # Make sure the server is reachable before continuing
    msg = ('Server %s is not reachable' % url)
    if not is_server_reachable(url):
        raise Exception(msg)

    wcs_reader = MetadataReader(url, 'wcs', version)
    wfs_reader = MetadataReader(url, 'wfs', version)
    layers = []
    layers.extend(wfs_reader.get_metadata())
    layers.extend(wcs_reader.get_metadata())
    return layers


class MetadataReader(object):
    """Read and parse capabilities document into a lxml.etree infoset

       Adapted from:
       http://trac.gispython.org/lab/browser/OWSLib/trunk/
              owslib/feature/wfs200.py#L402
    """

    def __init__(self, server_url, service_type, version):
        """Initialize"""
        self.WFS_NAMESPACE = '{http://www.opengis.net/wfs}'
        self.WCS_NAMESPACE = '{http://www.opengis.net/wcs}'
        self.url = server_url
        self.service_type = service_type.lower()
        self.version = version
        self.xml = None
        if self.service_type == 'wcs':
            self.typelist = 'ContentMetadata'
            self.typeelms = 'CoverageOfferingBrief'
            self.namestr = 'name'
            self.titlestr = 'label'
            self.NAMESPACE = self.WCS_NAMESPACE
            self.keywordstr = 'keywords'
            self.abstractstr = 'description'
            self.layer_type = 'raster'
        elif self.service_type == 'wfs':
            self.typelist = 'FeatureTypeList'
            self.typeelms = 'FeatureType'
            self.namestr = 'Name'
            self.titlestr = 'Title'
            self.abstractstr = 'Abstract'
            self.NAMESPACE = self.WFS_NAMESPACE
            self.keywordstr = 'Keywords'
            self.layer_type = 'feature'
        else:
            msg = 'Unknown service type: "%s"' % self.service_type
            raise NotImplemented(msg)

    def capabilities_url(self):
        """Return a capabilities url
        """
        qs = []
        if self.url.find('?') != -1:
            qs = cgi.parse_qsl(self.url.split('?')[1])

        params = [x[0] for x in qs]

        if 'service' not in params:
            qs.append(('service', self.service_type))
        if 'request' not in params:
            qs.append(('request', 'GetCapabilities'))
        if 'version' not in params:
            qs.append(('version', self.version))

        urlqs = urlencode(tuple(qs))
        return self.url.split('?')[0] + '?' + urlqs

    def read(self):
        """Get and parse a WFS capabilities document, returning an
        instance of WFSCapabilitiesInfoset

        Parameters
        ----------
        url : string
            The URL to the WFS capabilities document.
        """
        request = self.capabilities_url()
        try:
            u = urlopen(request)
        except Exception, e:
            msg = ('Can not complete the request to %s, error was %s.'
                   % (request, str(e)))
            e.args = (msg,)
            raise
        else:
            response = u.read()
            # FIXME: Make sure it is not an html page with an error message.
            self.xml = response
            return etree.fromstring(self.xml)

    def readString(self, st):
        """Parse a WFS capabilities document, returning an
        instance of WFSCapabilitiesInfoset

        string should be an XML capabilities document
        """
        if not isinstance(st, str):
            raise ValueError('String must be of type string, '
                             'not %s' % type(st))
        return etree.fromstring(st)

    def get_metadata(self):

        _capabilities = self.read()
        request_url = self.capabilities_url()
        serviceidentelem = _capabilities.find(self.NAMESPACE + 'Service')
        featuretypelistelem = _capabilities.find(self.NAMESPACE +\
                                                     self.typelist)

        msg = ('Could not find element "%s" in namespace %s on %s'
               % (self.typelist, self.NAMESPACE, self.url))
        assert featuretypelistelem is not None, msg

        featuretypeelems = featuretypelistelem.findall(self.NAMESPACE +\
                                                           self.typeelms)
        layers = []
        for f in featuretypeelems:
            metadata = {'layer_type': self.layer_type}
            name = f.findall(self.NAMESPACE + self.namestr)
            title = f.findall(self.NAMESPACE + self.titlestr)
            kwds = f.findall(self.NAMESPACE + self.keywordstr)
            abstract = f.findall(self.NAMESPACE + self.abstractstr)

            layer_name = name[0].text
            #workspace_name = 'geonode' # FIXME (Ole): This is not used

            metadata['title'] = title[0].text

            if self.service_type == 'wcs':
                kwds = kwds[0].findall(self.NAMESPACE + 'keyword')

            if kwds is not None:
                for kwd in kwds[:]:
                    # Split all the kepairs
                    keypairs = str(kwd.text).split(',')
                    for val in keypairs:
                        # Only use keywords containing at least one :
                        if str(val).find(':') > -1:
                            k, v = val.split(':')
                            metadata[k.strip()] = v.strip()

            layers.append([layer_name, metadata])
        return layers


def write_keywords(keywords, filename):
    """Write keywords dictonary to file

    Input
        keywords: Dictionary of keyword, value pairs
        filename: Name of keywords file. Extension expected to be .keywords

    Keys must be strings
    Values must be strings or None.

    If value is None, only the key will be written. Otherwise key, value pairs
    will be written as key: value

    Trailing or preceding whitespace will be ignored.
    """

    # Input checks
    basename, ext = os.path.splitext(filename)

    msg = ('Unknown extension for file %s. '
           'Expected %s.keywords' % (filename, basename))
    assert ext == '.keywords', msg

    # Write
    fid = open(filename, 'w')
    for k, v in keywords.items():

        msg = ('Key in keywords dictionary must be a string. '
               'I got %s with type %s' % (k, type(k)))
        assert isinstance(k, basestring), msg

        key = k.strip()

        msg = ('Key in keywords dictionary must not contain the ":" '
               'character. I got "%s"' % key)
        assert ':' not in key, msg

        if v is None:
            fid.write('%s\n' % key)
        else:
            val = v.strip()

            msg = ('Value in keywords dictionary must be a string or None. '
                   'I got %s with type %s' % (val, type(val)))
            assert isinstance(val, basestring), msg

            msg = ('Value must not contain the ":" character. '
                   'I got "%s"' % val)
            assert ':' not in val, msg

            fid.write('%s: %s\n' % (key, val))
    fid.close()


def read_keywords(filename):
    """Read keywords dictonary from file

    Input
        filename: Name of keywords file. Extension expected to be .keywords
                  The format of one line is expected to be either
                  string: string
                  or
                  string
    Output
        keywords: Dictionary of keyword, value pairs
    """

    # Input checks
    basename, ext = os.path.splitext(filename)

    msg = ('Unknown extension for file %s. '
           'Expected %s.keywords' % (filename, basename))
    assert ext == '.keywords', msg

    if not os.path.isfile(filename):
        return {}

    # Read
    keywords = {}
    fid = open(filename, 'r')
    for line in fid.readlines():
        text = line.strip()
        if text == '':
            continue

        fields = text.split(':')

        msg = ('Keyword must be either "string" or "string: string". '
               'I got %s ' % text)
        assert len(fields) in [1, 2], msg

        key = fields[0].strip()

        if len(fields) == 2:
            val = fields[1].strip()
        else:
            val = None

        keywords[key] = val
    fid.close()

    return keywords
