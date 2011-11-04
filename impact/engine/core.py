"""Computational engine for Risk in a Box core.

Provides the function calculate_impact()
"""

import sys
import numpy

from impact.storage.projection import Projection
from impact.storage.projection import DEFAULT_PROJECTION
from impact.storage.utilities import unique_filename
from impact.storage.utilities import bbox_intersection
from impact.storage.utilities import buffered_bounding_box
from impact.storage.io import bboxlist2string, bboxstring2list
from impact.storage.io import check_bbox_string

import logging
logger = logging.getLogger('risiko')

def calculate_impact(layers, impact_fcn,
                     comment=''):
    """Calculate impact levels as a function of list of input layers

    Input
        FIXME (Ole): For the moment we take only a list with two
        elements containing one hazard level one exposure level

        layers: List of Raster and Vector layer objects to be used for analysis

        impact_fcn: Function of the form f(layers)
        comment:

    Output
        filename of resulting impact layer (GML). Comment is embedded as
        metadata. Filename is generated from input data and date.

    Note
        The admissible file types are tif and asc/prj for raster and
        gml or shp for vector data

    Assumptions
        1. All layers are in WGS84 geographic coordinates
        2. Layers are equipped with metadata such as names and categories
    """

    # Input checks
    check_data_integrity(layers)

    # Get an instance of the passed impact_fcn
    impact_function = impact_fcn()

    # Pass input layers to plugin

    # FIXME (Ole): When issue #21 has been fully implemented, this
    #              return value should be a list of layers.
    F = impact_function.run(layers)

    # Write result and return filename
    if F.is_raster:
        extension = '.tif'
        # use default style for raster
    else:
        extension = '.shp'
        # use default style for vector

    output_filename = unique_filename(suffix=extension)
    F.write_to_file(output_filename)

    # Generate style as defined by the impact_function
    style = impact_function.generate_style(F)
    f = open(output_filename.replace(extension, '.sld'), 'w')
    f.write(style)
    f.close()

    return output_filename


def check_data_integrity(layer_files):
    """Read list of layer files and verify that that they have the same
    projection and georeferencing.
    """

    # Set default values for projection and geotransform.
    # Enforce DEFAULT (WGS84).
    # Choosing 'None' will use value of first layer.
    reference_projection = Projection(DEFAULT_PROJECTION)
    geotransform = None
    coordinates = None

    for layer in layer_files:

        # Ensure that projection is consistent across all layers
        if reference_projection is None:
            reference_projection = layer.projection
        else:
            msg = ('Projections in input layer %s is not as expected:\n'
                   'projection: %s\n'
                   'default:    %s'
                   '' % (layer, layer.projection, reference_projection))
            assert reference_projection == layer.projection, msg

        # Ensure that geotransform and dimensions is consistent across
        # all *raster* layers
        if layer.is_raster:
            if geotransform is None:
                geotransform = layer.get_geotransform()
            else:
                msg = ('Geotransforms in input raster layers are different: '
                       '%s %s' % (geotransform, layer.get_geotransform()))
                # FIXME (Ole): Use high tolerance until we find out
                # why geoserver changes resolution.
                assert numpy.allclose(geotransform,
                                      layer.get_geotransform(),
                                      rtol=1.0e-1), msg

        # In either case of vector layers, we check that the coordinates
        # are the same
        if layer.is_vector:
            if coordinates is None:
                coordinates = layer.get_geometry()
            else:
                msg = ('Coordinates in input vector layers are different: '
                       '%s %s' % (coordinates, layer.get_geometry()))
                assert numpy.allclose(coordinates,
                                      layer.get_geometry()), msg

            msg = ('There are no data points to interpolate to. '
                   'Perhaps zoom out or pan to the study area '
                   'and try again')
            assert len(layer) > 0, msg

    # Check that arrays are aligned.
    #
    # We have observerd Geoserver resolution changes - see ticket:102
    # https://github.com/AIFDR/riab/issues/102
    #
    # However, both rasters are now downloaded with exactly the same
    # parameters since we have made bbox and resolution variable in ticket:103
    # https://github.com/AIFDR/riab/issues/103
    #
    # So if they are still not aligned, we raise an Exception

    # First find the minimum dimensions
    M = N = sys.maxint
    refname = ''
    for layer in layer_files:
        if layer.is_raster:
            if layer.rows < M:
                refname = layer.get_name()
                M = layer.rows
            if layer.columns < N:
                refname = layer.get_name()
                N = layer.columns

    # Then check for alignment
    for layer in layer_files:
        if layer.is_raster:
            data = layer.get_data()

            msg = ('Rasters are not aligned!\n'
                   'Raster %s has %i rows but raster %s has %i rows\n'
                   'Refer to issue #102' % (layer.get_name(),
                                            layer.rows,
                                            refname, M))
            assert layer.rows == M, msg

            msg = ('Rasters are not aligned!\n'
                   'Raster %s has %i columns but raster %s has %i columns\n'
                   'Refer to issue #102' % (layer.get_name(),
                                            layer.columns,
                                            refname, N))
            assert layer.columns == N, msg


def get_common_resolution(haz_metadata, exp_metadata):
    """Determine common resolution for raster layers

    Input
        haz_metadata: Metadata for hazard layer
        exp_metadata: Metadata for exposure layer

    Output
        raster_resolution: Common resolution or None (in case of vector layers)
    """

    # Determine resolution in case of raster layers
    haz_res = exp_res = None
    if haz_metadata['layer_type'] == 'raster':
        haz_res = haz_metadata['resolution']

    if exp_metadata['layer_type'] == 'raster':
        exp_res = exp_metadata['resolution']

    # Determine common resolution in case of two raster layers
    if haz_res is None or exp_res is None:
        # This means native resolution will be used
        raster_resolution = None
    else:
        # Take the minimum
        resx = min(haz_res[0], exp_res[0])
        resy = min(haz_res[1], exp_res[1])

        raster_resolution = (resx, resy)

    return raster_resolution


def get_bounding_boxes(haz_metadata, exp_metadata, req_bbox):
    """Check and get appropriate bounding boxes for input layers

    Input
        haz_metadata: Metadata for hazard layer
        exp_metadata: Metadata for exposure layer
        req_bbox: Bounding box (string) as requested by HTML POST.

    Output
        haz_bbox: Bounding box to be used for hazard layer.
        exp_bbox: Bounding box to be used for exposure layer
        imp_bbox: Bounding box to be used for resulting impact layer

    Note exp_bbox and imp_bbox are the same and calculated as the
         intersection among hazard, exposure and viewport bounds.
         haz_bbox may be grown by one pixel size in case exposure data
         is vector data to make sure points always can be interpolated
    """

    # Input checks
    msg = ('Invalid bounding box %s (%s). '
           'It must be a string' % (str(req_bbox), type(req_bbox)))
    assert isinstance(req_bbox, basestring), msg
    check_bbox_string(req_bbox)

    # Get bounding boxes for layers and viewport
    haz_bbox = haz_metadata['bounding_box']
    exp_bbox = exp_metadata['bounding_box']
    vpt_bbox = bboxstring2list(req_bbox)

    # New bounding box for data common to hazard, exposure and viewport
    # Download only data within this intersection
    intersection_bbox = bbox_intersection(vpt_bbox, haz_bbox, exp_bbox)
    if intersection_bbox is None:
        # Bounding boxes did not overlap
        msg = ('Bounding boxes of hazard data [%s], exposure data [%s] '
               'and viewport [%s] did not overlap, so no computation was '
               'done. Please make sure you pan to where the data is and '
               'that hazard and exposure data overlaps.'
               % (bboxlist2string(haz_bbox, decimals=3),
                  bboxlist2string(exp_bbox, decimals=3),
                  bboxlist2string(vpt_bbox, decimals=3)))
        logger.info(msg)
        raise Exception(msg)

    # Grow hazard bbox to buffer this common bbox in case where
    # hazard is raster and exposure is vector
    if (haz_metadata['layer_type'] == 'raster' and
        exp_metadata['layer_type'] == 'vector'):

        haz_res = haz_metadata['resolution']
        haz_bbox = buffered_bounding_box(intersection_bbox, haz_res)
    else:
        haz_bbox = intersection_bbox

    # Usually the intersection bbox is used for both exposure layer and result
    exp_bbox = imp_bbox = intersection_bbox

    return haz_bbox, exp_bbox, imp_bbox
