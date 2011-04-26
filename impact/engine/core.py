"""Computational engine for Risk in a Box core.

Provides the function calculate_impact()
"""

import os
import io
import numpy

from impact.storage.projection import Projection
from impact.storage.utilities import unique_filename
from impact.storage.utilities import DEFAULT_PROJECTION


def calculate_impact(layers, impact_function,
                     comment=''):
    """Calculate impact levels as a function of list of input layers

    Input

        FIXME (Ole): For the moment we take only a list with two
        elements containing one hazard level one xposure level

        FIXME: This is has been reverted back to single names, so the doc
        string below is not current.

        impact_function: Function of the form f(H, E) where H and E are
                         dictionaries of aligned numpy arrays named the same
                         way as the input layers
        comment:

    Output
        filename of resulting impact layer (GML). Comment is embedded as
        metadata. Filename is generated from input data and date.


    # FIXME (Ole): Redo doc string to reflect ticket #21
    Note
        The admissible file types are tif and asc/prj for coverages and
        gml (or shp?) for vector data

    Assumptions
        1. Input layer files are either geotiff (for raster data) or
           gml (for vector data)
        2. All layers are in WGS84 geographic coordinates
        3. Layers are named (either as dictionaries or using the internal
           naming structure of geotiff and gml)

    This function delegates work to internal functions depending on types
    of hazard and exposure data.
    """

    # Input checks
    check_data_integrity(layers)

    # Pass input layers to plugin
    F = impact_function.run(layers)

    # Write result and return filename
    # FIXME (Ole): Maybe this filename should be defined in the plugin
    #              Oh Yes it should.
    # FIXME (Ole): When issue #21 has been fully implemented, this
    #              return value should be a list of layers.

    if F.is_raster:
        extension = '.tif'
        # use default style for raster
    else:
        extension = '.shp'
        # use default style for vector

    output_filename = unique_filename(suffix=extension)

    style = impact_function.generate_style(F)
    f = open(output_filename.replace(extension, '.sld'), 'w')
    f.write(style)
    f.close()
    F.write_to_file(output_filename)
    return output_filename


def check_data_integrity(layer_files):
    """Read list of layer files and verify that that they have the same
    projection and georeferencing.
    """

    # Set default values for projection and geotransform.
    # Choosing 'None' will use value of first layer.
    projection = Projection(DEFAULT_PROJECTION)
    geotransform = None
    coordinates = None

    for filename in layer_files:

        # Extract data
        layer = filename

        # Ensure that projection is consistent across all layers
        if projection is None:
            projection = layer.projection
        else:
            msg = ('Projections in input layer %s is not as expected:\n'
                   'projection: %s\n'
                   'default:    %s'
                   '' % (filename,
                         projection.get_projection(proj4=True),
                         layer.projection.get_projection(proj4=True)))
            assert projection == layer.projection, msg

        # Ensure that geotransform is consistent across all *raster* layers
        if layer.is_raster:
            if geotransform is None:
                geotransform = layer.get_geotransform()
            else:
                msg = ('Geotransforms in input raster layers are different: '
                       '%s %s' % (geotransform, layer.get_geotransform()))
                assert geotransform == layer.get_geotransform(), msg

        # In case of vector layers, we check that the coordinates
        # are the same
        if layer.is_vector:
            if coordinates is None:
                coordinates = layer.get_geometry()
            else:
                msg = ('Coordinates in input vector layers are different: '
                       '%s %s' % (coordinates, layer.get_geometry()))
                assert numpy.allclose(coordinates,
                                      layer.get_geometry()), msg
