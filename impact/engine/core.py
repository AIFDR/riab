"""Computational engine for Risk in a Box core.

Provides the function calculate_impact()
"""

import sys
import numpy

from impact.storage.projection import Projection
from impact.storage.utilities import unique_filename
from impact.storage.utilities import DEFAULT_PROJECTION


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

    # FIXME (Ole): Hack due to Geoserver resolution changes,
    #              This will ensure alignment of arrays to the first
    #              encountered
    #              This is truly horrible!!!!!!!!!!

    # First find the minimum dimensions
    dimensions = [sys.maxint, sys.maxint]
    for layer in layer_files:

        if layer.is_raster:
            if layer.rows < dimensions[0]:
                dimensions[0] = layer.rows
            if layer.columns < dimensions[1]:
                dimensions[1] = layer.columns

    # Make sure all rasters are clipped to the same box
    for layer in layer_files:

        if layer.is_raster:
            data = layer.get_data()

            layer.rows = dimensions[0]
            layer.columns = dimensions[1]

            # XTreme Monkey Patching!
            layer.data = data[0:layer.rows, 0:layer.columns]
