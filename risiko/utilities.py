from geonode.maps.utils import file_upload, GeoNodeException
from impact.storage.utilities import LAYER_TYPES, unique_filename
from impact.storage.io import read_layer, download, get_bounding_box, get_ows_metadata
import numpy
import time
import os

import settings
INTERNAL_SERVER_URL = os.path.join(settings.GEOSERVER_BASE_URL, 'ows')

import logging
logger = logging.getLogger('risiko')


class RisikoException(Exception):
    pass


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
    try:
        metadata = get_ows_metadata(INTERNAL_SERVER_URL, layer_name)
    except:
        # Convert any exception to AssertionError for use in retry loop in
        # save_file_to_geonode.
        raise AssertionError

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
    except GeoNodeException, e:
        # Layer did not upload. Convert GeoNodeException to RisikoException
        raise RisikoException(e)
    except Exception, e:
        # Unknown problem. Re-raise
        raise
    else:
        # Check and return layer object
        ok = False
        for i in range(4):
            try:
                check_layer(layer)
            except AssertionError, e:
                time.sleep(0.3)
            else:
                ok = True
                break
        if ok:
            return layer
        else:
            msg = ('Could not confirm that layer %s was uploaded '
                   'correctly: %s' % (layer, e))
            raise Exception(msg)
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
