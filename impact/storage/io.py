"""IO module for reading and writing of files

   This module provides functionality to read and write
   raster and vector layers from numerical data.
"""

import os
import time
import numpy
import urllib2
import tempfile
import contextlib
from zipfile import ZipFile

from impact.storage.vector import Vector
from impact.storage.raster import Raster
from impact.storage.utilities import get_layers_metadata, geotransform2bbox
from impact.storage.utilities import LAYER_TYPES
from impact.storage.utilities import unique_filename

from owslib.wcs import WebCoverageService
from owslib.wfs import WebFeatureService

from geonode.maps.utils import file_upload, GeoNodeException
from django.conf import settings

import logging
logger = logging.getLogger('risiko')

INTERNAL_SERVER_URL = os.path.join(settings.GEOSERVER_BASE_URL, 'ows')


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


def write_raster_data(data, projection, geotransform, filename, keywords=None):
    """Write array to raster file with specified metadata and one data layer

    Input:
        data: Numpy array containing grid data
        projection: WKT projection information
        geotransform: 6 digit vector
                      (top left x, w-e pixel resolution, rotation,
                       top left y, rotation, n-s pixel resolution).
                       See e.g. http://www.gdal.org/gdal_tutorial.html
        filename: Output filename
        keywords: Optional dictionary

    Note: The only format implemented is GTiff and the extension must be .tif
    """

    R = Raster(data, projection, geotransform, keywords=keywords)
    R.write_to_file(filename)


def write_point_data(data, projection, geometry, filename, keywords=None):
    """Write point data and any associated attributes to vector file

    Input:
        data: List of N dictionaries each with M fields where
              M is the number of attributes.
              A value of None is acceptable.
        projection: WKT projection information
        geometry: Nx2 Numpy array with longitudes, latitudes
                  N is the number of points (features).
        filename: Output filename
        keywords: Optional dictionary

    Note: The only format implemented is GML and SHP so the extension
    must be either .gml or .shp

    # FIXME (Ole): When the GML driver is used,
    #              the spatial reference is not stored.
    #              I suspect this is a bug in OGR.

    Background:
    * http://www.gdal.org/ogr/ogr_apitut.html (last example)
    * http://invisibleroads.com/tutorials/gdal-shapefile-points-save.html
    """

    V = Vector(data, projection, geometry, keywords=keywords)
    V.write_to_file(filename)

# FIXME (Ole): Why is the resolution hard coded here (issue #103)
WCS_TEMPLATE = '%s?version=1.0.0' + \
                      '&service=wcs&request=getcoverage&format=GeoTIFF&' + \
                      'store=false&coverage=%s&crs=EPSG:4326&bbox=%s' + \
                      '&resx=0.008333333333000&resy=0.008333333333000'

# FIXME (Ole): Why is maxFeatures hard coded?
WFS_TEMPLATE = '%s?service=WFS&version=1.0.0' + \
               '&request=GetFeature&typeName=%s' + \
               '&outputFormat=SHAPE-ZIP&bbox=%s'


def get_bounding_box(filename):
    """Get bounding box for specified raster or vector file

    Input:
        filename

    Output:
        bounding box as python list [West, South, East, North]
    """

    layer = read_layer(filename)
    return layer.get_bounding_box()


def bboxlist2string(bbox):
    """Convert bounding box list to comma separated string

    Input
        bbox: List of coordinates of the form [W, S, E, N]
    Output
        bbox_string: Format 'W,S,E,N' - each will have 6 decimal points
    """

    msg = 'Got string %s, but expected bounding box as a list' % str(bbox)
    assert not isinstance(bbox, basestring), msg

    try:
        bbox = list(bbox)
    except:
        msg = 'Could not coerce bbox %s into a list' % str(bbox)
        raise Exception(msg)

    msg = ('Bounding box must have 4 coordinates [W, S, E, N]. '
           'I got %s' % str(bbox))
    assert len(bbox) == 4, msg

    for x in bbox:
        try:
            float(x)
        except ValueError, e:
            msg = ('Bounding box %s contained non-numeric entry %s, '
                   'original error was "%s".' % (bbox, x, e))
            raise AssertionError(msg)

    return '%.6f,%.6f,%.6f,%.6f' % tuple(bbox)


def bboxstring2list(bbox_string):
    """Convert bounding box string to list

    Input
        bbox_string: String of bounding box coordinates of the form 'W,S,E,N'
    Output
        bbox: List of floating point numbers with format [W, S, E, N]
    """

    msg = ('Bounding box must be a string with coordinates following the '
           'format 105.592,-7.809,110.159,-5.647\n'
           'Instead I got %s of type %s.' % (str(bbox_string),
                                             type(bbox_string)))
    assert isinstance(bbox_string, basestring), msg

    fields = bbox_string.split(',')
    msg = ('Bounding box string must have 4 coordinates in the form '
           '"W,S,E,N". I got bbox == "%s"' % bbox_string)
    assert len(fields) == 4, msg

    for x in fields:
        try:
            float(x)
        except ValueError, e:
            msg = ('Bounding box %s contained non-numeric entry %s, '
                   'original error was "%s".' % (bbox_string, x, e))
            raise AssertionError(msg)

    return [float(x) for x in fields]


def get_bounding_box_string(filename):
    """Get bounding box for specified raster or vector file

    Input:
        filename

    Output:
        bounding box as python string 'West, South, East, North'
    """

    return bboxlist2string(get_bounding_box(filename))


def get_geotransform(server_url, layer_name):
    """Constructs the geotransform based on the WCS service.

       Should only be called be rasters / WCS layers.

       Returns:
            geotransform is a vector of six numbers:

             (top left x, w-e pixel resolution, rotation,
              top left y, rotation, n-s pixel resolution).

            We should (at least) use elements 0, 1, 3, 5
            to uniquely determine if rasters are aligned

    """

    # FIXME (Ole): This should be superseded by new get_metadata
    #              function which will be entirely based on OWSLib
    #              Issue #95

    wcs = WebCoverageService(server_url, version='1.0.0')

    if layer_name in wcs.contents:
        layer = wcs.contents[layer_name]
        grid = layer.grid

        top_left_x = float(layer.grid.origin[0])
        we_pixel_res = float(layer.grid.offsetvectors[0][0])
        x_rotation = float(layer.grid.offsetvectors[0][1])
        top_left_y = float(layer.grid.origin[1])
        y_rotation = float(layer.grid.offsetvectors[1][0])
        ns_pixel_res = float(layer.grid.offsetvectors[1][1])

        # There is half a pixel_resolution difference between
        # what WCS reports and what GDAL reports.
        # A pixel CENTER vs pixel CORNER difference.
        adjusted_top_left_x = top_left_x - we_pixel_res / 2
        adjusted_top_left_y = top_left_y - ns_pixel_res / 2

        return (adjusted_top_left_x, we_pixel_res, x_rotation,
                adjusted_top_left_y, y_rotation, ns_pixel_res)
    else:
        msg = ('Could not find layer "%s" in the WCS server "%s".'
               'Available layers were: %s' % (layer_name, server_url,
                                              wcs.contents.keys()))
        raise Exception(msg)


def get_metadata(server_url, layer_name):
    """Uses OWS services to get the metadata for a given layer

    Input
        server_url:
        layer_name: must follow the convention workspace:name
    """

    # FIXME (Ole): This should be superseded by new get_metadata
    #              function which will be entirely based on OWSLib
    #              Issue #95

    # Get all metadata

    themetadata = get_layers_metadata(server_url, version='1.0.0')

    # Look for specific layer
    layer_metadata = None
    for x in themetadata:
        if x[0] == layer_name:
            # We expect only one element in this list, if there is more
            # than one, we will use the first one.
            layer_metadata = x[1]
            break

    msg = ('There is no metadata in server %s for layer '
           '%s. Available metadata is %s' % (server_url, layer_name,
                                             themetadata))
    assert layer_metadata is not None, msg

    # FIXME: We need a geotransform attribute in get_metadata
    # Let's add it here for the time being
    if layer_metadata['layer_type'] == 'raster':
        geotransform = get_geotransform(server_url, layer_name)

        layer_metadata['geotransform'] = geotransform
        #layer_metadata['bbox'] = geotransform2bbox(geotransform,
        #                                           columns, rows)

    return layer_metadata


def get_ows_metadata(server_url, layer_name):
    """Uses OWSLib to get the metadata for a given layer

    Input
        server_url: e.g. http://localhost:8001/geoserver-geonode-dev/ows
        layer_name: must follow the convention workspace:name

    Output
        metadata: Dictionary of metadata fields common to both
                  raster and vector layers
    """

    wcs = WebCoverageService(server_url, version='1.0.0')
    wfs = WebFeatureService(server_url, version='1.0.0')

    metadata = {}
    if layer_name in wcs.contents:
        layer = wcs.contents[layer_name]
        metadata['layer_type'] = 'raster'
    elif layer_name in wfs.contents:
        layer = wfs.contents[layer_name]
        metadata['layer_type'] = 'vector'
    else:
        msg = ('Layer %s was not found in WxS contents on server %s.\n'
               'WCS contents: %s\n'
               'WFS contents: %s\n' % (layer_name, server_url,
                                       wcs.contents, wfs.contents))
        raise Exception(msg)

    # Metadata common to both raster and vector data
    metadata['bounding_box'] = layer.boundingBoxWGS84
    metadata['title'] = layer.title
    metadata['id'] = layer.id

    # Extract keywords
    if not hasattr(layer, 'keywords'):
        msg = 'No keywords in %s. Submit patch to OWSLib maintainers' % layer
        # FIXME (Ole): Uncomment when OWSLib patch has been submitted
        #Raise Exception(msg)
    else:
        keyword_dict = {}
        for keyword in layer.keywords:
            if keyword is not None:
                # FIXME (Ole): Why would this be None sometimes?

                for keyword_string in keyword.split(','):

                    if ':' in keyword_string:
                        key, value = keyword_string.strip().split(':')
                        keyword_dict[key] = value
                    else:
                        keyword_dict[keyword_string] = None

        metadata['keywords'] = keyword_dict

    return metadata


def get_file(download_url, suffix):
    """Download a file from an HTTP server.
    """

    tempdir = '/tmp/%s' % str(time.time())
    os.mkdir(tempdir)
    t = tempfile.NamedTemporaryFile(delete=False,
                                    suffix=suffix,
                                    dir=tempdir)

    with contextlib.closing(urllib2.urlopen(download_url)) as f:
        data = f.read()

    if '<ServiceException>' in data:
        msg = ('File download failed.\n'
               'URL: %s\n'
               'Error message: %s' % (download_url, data))
        raise Exception(msg)

    # Write and return filename
    t.write(data)
    filename = os.path.abspath(t.name)
    return filename


def check_bbox_string(bbox_string):
    """Check that bbox string is valid
    """

    msg = 'Expected bbox as a string with format "W,S,E,N"'
    assert isinstance(bbox_string, basestring), msg

    # Use checks from string to list conversion
    minx, miny, maxx, maxy = bboxstring2list(bbox_string)

    # Check semantic integrity
    msg = ('Western border %.5f of bounding box %s was out of range '
           'for longitudes ([-180:180])' % (minx, bbox_string))
    assert -180 <= minx <= 180, msg

    msg = ('Eastern border %.5f of bounding box %s was out of range '
           'for longitudes ([-180:180])' % (maxx, bbox_string))
    assert -180 <= maxx <= 180, msg

    msg = ('Southern border %.5f of bounding box %s was out of range '
           'for latitudes ([-90:90])' % (miny, bbox_string))
    assert -90 <= miny <= 90, msg

    msg = ('Northern border %.5f of bounding box %s was out of range '
           'for latitudes ([-90:90])' % (maxy, bbox_string))
    assert -90 <= maxy <= 90, msg

    msg = ('Western border %.5f was greater than or equal to eastern border '
           '%.5f of bounding box %s' % (minx, maxx, bbox_string))
    assert minx < maxx, msg

    msg = ('Southern border %.5f was greater than or equal to northern border '
           '%.5f of bounding box %s' % (miny, maxy, bbox_string))
    assert miny < maxy, msg


def download(server_url, layer_name, bbox):
    """Download the source data of a given layer.

       Input
           server_url: String such as 'http://www.aifdr.org:8080/geoserver/ows'
           layer_name: Layer identifier of the form workspace:name,
                       e.g 'geonode:Earthquake_Ground_Shaking'
           bbox: Bounding box for layer. This can either be a string or a list
                 with format [west, south, east, north], e.g.
                 '87.998242,-8.269822,117.046094,5.097895'

       Layer type must be either 'vector' or 'raster'
    """

    # FIXME (Ole): Pass in resolution here

    # Input checks
    assert isinstance(server_url, basestring)
    try:
        urllib2.urlopen(server_url)
    except Exception, e:
        msg = ('Argument server_url doesn\'t appear to be a valid URL'
               'I got %s. Error message was: %s' % (server_url, str(e)))
        raise Exception(msg)

    msg = ('Expected layer_name to be a basestring. '
           'Instead got %s which is of type %s' % (layer_name,
                                                   type(layer_name)))
    assert isinstance(layer_name, basestring), msg

    msg = ('Argument layer name must have the form'
           'workspace:name. I got %s' % layer_name)
    assert len(layer_name.split(':')) == 2, msg

    if isinstance(bbox, list) or isinstance(bbox, tuple):
        bbox_string = bboxlist2string(bbox)
    elif isinstance(bbox, basestring):
        # Remove spaces if any (GeoServer freaks if string has spaces)
        bbox_string = ','.join([x.strip() for x in bbox.split(',')])
    else:
        msg = ('Bounding box must be a string or a list of coordinates with '
               'format [west, south, east, north]. I got %s' % str(bbox))
        raise Exception(msg)

    # Check integrity of bounding box
    check_bbox_string(bbox_string)

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


#--------------------------------------------------------------------
# Functionality to upload layers to GeoNode and check their integrity
#--------------------------------------------------------------------

class RisikoException(Exception):
    pass


def console_log():
    """Reconfigure logging to output to the console.
    """
    import logging
    for _module in ["risiko"]:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler())
        _logger.setLevel(logging.INFO)


def run(cmd, stdout=None, stderr=None):
    """Run command with stdout and stderr optionally redirected

    The logfiles are only kept in case the command fails.
    """

    # Build command
    msg = 'Argument cmd must be a string. I got %s' % cmd
    assert isinstance(cmd, basestring), msg

    s = cmd
    if stdout is not None:
        msg = 'Argument stdout must be a string or None. I got %s' % stdout
        assert isinstance(stdout, basestring), msg
        s += ' > %s' % stdout

    if stderr is not None:
        msg = 'Argument stderr must be a string or None. I got %s' % stdout
        assert isinstance(stderr, basestring), msg
        s += ' 2> %s' % stderr

    # Run command
    err = os.system(s)

    if err != 0:
        msg = 'Command "%s" failed with errorcode %i. ' % (cmd, err)
        if stdout:
            msg += 'See logfile %s for stdout details' % stdout
        if stderr is not None:
            msg += 'See logfile %s for stderr details' % stderr
        raise Exception(msg)
    else:
        # Clean up
        if stdout is not None:
            os.remove(stdout)
        if stderr is not None:
            os.remove(stderr)


def assert_bounding_box_matches(layer, filename):
    """Verify that GeoNode layer has the same bounding box as filename
    """

    # Check integrity
    assert hasattr(layer, 'geographic_bounding_box')
    assert isinstance(layer.geographic_bounding_box, basestring)

    # Exctract bounding bounding box from layer handle
    s = 'POLYGON(('
    i = layer.geographic_bounding_box.find(s) + len(s)
    assert i > len(s)

    j = layer.geographic_bounding_box.find('))')
    assert j > i

    bbox_string = str(layer.geographic_bounding_box[i:j])
    A = numpy.array([[float(x[0]), float(x[1])] for x in
                     (p.split() for p in bbox_string.split(','))])
    south = min(A[:, 1])
    north = max(A[:, 1])
    west = min(A[:, 0])
    east = max(A[:, 0])
    bbox = [west, south, east, north]

    # Check correctness of bounding box against reference
    ref_bbox = get_bounding_box(filename)

    msg = ('Bounding box from layer handle "%s" was not as expected.\n'
           'Got %s, expected %s' % (layer.name, bbox, ref_bbox))
    assert numpy.allclose(bbox, ref_bbox, rtol=1.0e-6, atol=1.0e-8), msg


def check_layer(layer, full=False):
    """Verify if an object is a valid Layer.

    If check fails an exception is raised.

    Input
        layer: Layer object
        full: Optional flag controlling whether layer is to be downloaded
              as part of the check.
    """

    from geonode.maps.models import Layer

    msg = ('Was expecting layer object, got None')
    assert layer is not None, msg
    msg = ('Was expecting layer object, got %s' % (type(layer)))
    assert type(layer) is Layer, msg
    msg = ('The layer does not have a valid name: %s' % layer.name)
    assert len(layer.name) > 0, msg
    msg = ('The layer does not have a valid workspace: %s' % layer.workspace)
    assert len(layer.workspace) > 0, msg

    # Get layer metadata
    layer_name = '%s:%s' % (layer.workspace, layer.name)
    metadata = get_ows_metadata(INTERNAL_SERVER_URL, layer_name)
    #try:
    #    metadata = get_ows_metadata(INTERNAL_SERVER_URL, layer_name)
    #except:
    #    # Convert any exception to AssertionError for use in retry loop in
    #    # save_file_to_geonode.
    #    raise AssertionError

    assert 'id' in metadata
    assert 'title' in metadata
    assert 'layer_type' in metadata
    assert 'keywords' in metadata
    assert 'bounding_box' in metadata

    # Get bounding box and download
    bbox = metadata['bounding_box']
    assert len(bbox) == 4

    if full:
        # Check that layer can be downloaded again
        downloaded_layer = download(INTERNAL_SERVER_URL, layer_name, bbox)
        assert os.path.exists(downloaded_layer.filename)

        # Check integrity between Django layer and file
        assert_bounding_box_matches(layer, downloaded_layer.filename)

        # Read layer and verify
        L = read_layer(downloaded_layer.filename)

        # Could do more here
        #print dir(L)
        #print L.keywords  #FIXME(Ole): I don't think keywords are downloaded!
        #print metadata['keywords']


def save_file_to_geonode(filename, user=None, title=None,
                         overwrite=True):
    """Save a single layer file to local Risiko GeoNode

    Input
        filename: Layer filename of type as defined in LAYER_TYPES
        user: Django User object
        title: String describing the layer.
               If None or '' the filename will be used.
        overwrite: Boolean variable controlling whether existing layers
                   can be overwritten by this operation. Default is True
    Output
        layer object
    """

    # Extract fully qualified basename and extension
    basename, extension = os.path.splitext(filename)

    if extension not in LAYER_TYPES:
        msg = ('Invalid file extension in file %s. Valid extensions are '
               '%s' % (filename, str(LAYER_TYPES)))
        raise RisikoException(msg)

    # Use file name to derive title if not specified
    if title is None or title == '':
        title = os.path.split(basename)[-1]

    # Try to find a file with a .keywords extension
    # and create a keywords list from there.
    # It is assumed that the keywords are separated
    # by new lines.
    # Empty keyword lines are ignored (as this causes issues downstream)
    keyword_list = []
    keyword_file = basename + '.keywords'
    if os.path.exists(keyword_file):
        f = open(keyword_file, 'r')
        for line in f.readlines():

            # Ignore blank lines
            raw_keyword = line.strip()
            if raw_keyword == '':
                continue

            # Strip any spaces after or before the colons if present
            if ':' in raw_keyword:
                keyword = ':'.join([x.strip() for x in raw_keyword.split(':')])

            # Store keyword
            keyword_list.append(keyword)
        f.close()

    # Take care of file types
    if extension == '.asc':
        # We assume this is an AAIGrid ASCII file such as those generated by
        # ESRI and convert it to Geotiff before uploading.

        # Create temporary tif file for upload and check that the road is clear
        prefix = os.path.split(basename)[-1]
        upload_filename = unique_filename(prefix=prefix, suffix='.tif')
        upload_basename, extension = os.path.splitext(upload_filename)

        # Copy any metadata files to unique filename
        for ext in ['.sld', '.keywords']:
            if os.path.exists(basename + ext):
                cmd = 'cp %s%s %s%s' % (basename, ext, upload_basename, ext)
                run(cmd)

        # Check that projection file exists
        prjname = basename + '.prj'
        if not os.path.isfile(prjname):
            msg = ('File %s must have a projection file named '
                   '%s' % (filename, prjname))
            raise RisikoException(msg)

        # Convert ASCII file to GeoTIFF
        R = read_layer(filename)
        R.write_to_file(upload_filename)
    else:
        # The specified file is the one to upload
        upload_filename = filename

    # Attempt to upload the layer
    try:
        # Upload
        layer = file_upload(upload_filename,
                            user=user,
                            title=title,
                            keywords=keyword_list,
                            overwrite=overwrite)
        layer.keywords = ' '.join(keyword_list)
        layer.save()
    except GeoNodeException, e:
        # Layer did not upload. Convert GeoNodeException to RisikoException
        raise RisikoException(e)
    except Exception, e:
        # Unknown problem. Re-raise
        raise
    else:
        time.sleep(1)
        logger.info('Uploaded "%s" with name "%s"', basename, layer.name)
        return layer
        # Check and return layer object
        # ok = False
        # for i in range(4):
        #     try:
        #         check_layer(layer)
        #     except AssertionError, e:
        #         time.sleep(0.3)
        #     else:
        #         ok = True
        #         break
        # if ok:
        #     return layer
        # else:
        #     msg = ('Could not confirm that layer %s was uploaded '
        #            'correctly: %s' % (layer, e))
        #    raise Exception(msg)
    finally:
        # Clean up generated tif files in either case
        if extension == '.asc':
            os.remove(upload_filename)
            os.remove(upload_filename + '.aux.xml')


def save_directory_to_geonode(directory,
                              user=None,
                              title=None,
                              overwrite=True):
    """Upload a directory of spatial data files to GeoNode

    Input
        directory: Valid root directory for layer files
        user: Django User object
        overwrite: Boolean variable controlling whether existing layers
                   can be overwritten by this operation. Default is True
    Output
        list of layer objects
    """

    msg = ('Argument %s to save_directory_to_geonode is not a valid directory.'
           % directory)
    assert os.path.isdir(directory), msg

    layers = []
    for root, dirs, files in os.walk(directory):
        for short_filename in files:
            basename, extension = os.path.splitext(short_filename)
            filename = os.path.join(root, short_filename)

            # Attempt upload only if extension is recognised
            if extension in LAYER_TYPES:
                try:
                    layer = save_to_geonode(filename,
                                            user=user,
                                            title=title,
                                            overwrite=overwrite)

                except Exception, e:
                    msg = ('Filename "%s" could not be uploaded. '
                           'Error was: %s' % (filename, str(e)))
                    # FIXME (Ole): Bring back when we can control
                    #              logging so as not to pollute test output
                    #logger.info(msg)
                else:
                    layers.append(layer)

    # Return layers that successfully uploaded
    return layers


def save_to_geonode(incoming, user=None, title=None, overwrite=True):
    """Save a files to local Risiko GeoNode

    Input
        incoming: Either layer file or directory
        user: Django User object
        title: If specified, it will be applied to all files. If None or ''
               filenames will be used to infer titles.
        overwrite: Boolean variable controlling whether existing layers
                   can be overwritten by this operation. Default is True

        FIXME (Ole): WxS contents does not reflect the renaming done
                     when overwrite is False. This should be reported to
                     the geonode-dev mailing list

    Output
        layer object or list of layer objects
    """

    msg = ('First argument to save_to_geonode must be a string. '
           'I got %s' % incoming)
    assert isinstance(incoming, basestring), msg

    if os.path.isdir(incoming):
        # Upload all valid layer files in this dir recursively

        layers = save_directory_to_geonode(incoming, title=title, user=user,
                                           overwrite=overwrite)
        return layers
    elif os.path.isfile(incoming):
        # Upload single file (using its name as title)
        basename, ext = os.path.splitext(incoming)

        layer = save_file_to_geonode(incoming, title=title, user=user,
                                     overwrite=overwrite)
        return layer
    else:
        msg = 'Argument %s was neither a file or a directory' % incoming
        raise RisikoException(msg)
