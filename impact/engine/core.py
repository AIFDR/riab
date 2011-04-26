"""Computational engine for Risk in a Box core.

Provides the function calculate_impact()
"""

import os
import io
import numpy

from impact.storage.raster import Raster
from impact.storage.vector import Vector
from impact.storage.projection import Projection
from impact.storage.io import read_layer
from impact.storage.io import write_point_data
from impact.storage.io import write_coverage
from impact.storage.utilities import unique_filename
from impact.storage.utilities import DEFAULT_PROJECTION
from impact.engine.interpolation import raster_spline

from impact.storage.utilities import unique_filename


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

    FIXME: Need to decide whether to use multiple files, multiple bands
           or both. Same with vector data.
    FIXME: Do we want a bounding box at this level. I think not.

    FIXME: Need to deal with values like -9999 for nodata here.
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

    if F.__class__ == Raster:
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


def read_hazard_data(hazard_levels):
    """Read hazard levels from files

    Note: Only raster formats are currently allowed
    """

    hazard_layers = {}
    for hazard_name in hazard_levels:

        # Extract data
        filename = hazard_levels[hazard_name]
        layer = filename
        if layer.is_vector:
            msg = ('Hazard layer %s is vector data. Only raster '
                   'data are allowed for Hazard layers' % filename)
            raise Exception(msg)

        hazard_layers[hazard_name] = layer

    return hazard_layers


def read_exposure_data(exposure_levels):
    """Read exposure levels from files
    """

    exposure_layers = {}
    for exposure_name in exposure_levels:

        # Extract data
        filename = exposure_levels[exposure_name]
        layer = filename

        exposure_layers[exposure_name] = layer

    return exposure_layers


# OBSOLETE ---------------------------------------
def Xcall_impact_function(layers,
                         impact_function,
                         name=''):
    """Extract numerical data from all layers and call impact function

    Both hazard and exposure data are assumed to be of same type
    and aligned
    """

    L = hazard_layers.values()[0]
    if L.is_raster:
        return call_impact_function_raster(impact_function,
                                           hazard_layers,
                                           exposure_layers,
                                           name)

    if L.is_vector:
        return call_impact_function_vector(impact_function,
                                           hazard_layers,
                                           exposure_layers,
                                           name)


def Xcall_impact_function_raster(impact_function,
                                hazard_layers,
                                exposure_layers,
                                impact_name=''):
    """Extract numerical data from all layers and call impact function

    Both hazard and exposure data are assumed to be raster data
    Result is also a raster data set.
    """

    # FIXME (Ole): Replace NODATA with 0 (nan=0) until we can
    #              handle proper NaN
    hazard_data = {}
    for name in hazard_layers:
        hazard_data[name] = hazard_layers[name].get_data(nan=0)
        assert hazard_layers[name].is_raster

    exposure_data = {}
    for name in exposure_layers:
        exposure_data[name] = exposure_layers[name].get_data(nan=0)
        assert exposure_layers[name].is_raster

        projection = exposure_layers[name].get_projection()
        geotransform = exposure_layers[name].get_geotransform()

    # FIXME: Use only one layer at a time for the time being
    H = hazard_data.values()[0]
    E = exposure_data.values()[0]

    F = impact_function.run(H, E)

    R = Raster(F, projection, geotransform, impact_name)
    return R


def Xcall_impact_function_vector(impact_function,
                                hazard_layers,
                                exposure_layers,
                                impact_name=''):
    """Extract numerical data from all layers and call impact function

    Both hazard and exposure data are assumed to be vector data
    Result is also a vector data set.
    """

    coordinates = None
    hazard_data = {}
    for name in hazard_layers:
        C = hazard_layers[name].get_geometry()
        D = hazard_layers[name].get_data()
        hazard_data[name] = C, D
        assert hazard_layers[name].is_vector

        # SANITY
        if coordinates is None:
            coordinates = hazard_layers[name].get_geometry()
        else:
            assert numpy.allclose(coordinates,
                                  hazard_layers[name].get_geometry())

    exposure_data = {}
    for name in exposure_layers:

        C = exposure_layers[name].get_geometry()
        D = exposure_layers[name].get_data()
        exposure_data[name] = C, D
        assert exposure_layers[name].is_vector

        projection = exposure_layers[name].get_projection()

        # SANITY
        if coordinates is None:
            coordinates = exposure_layers[name].get_geometry()
        else:
            assert numpy.allclose(coordinates,
                                  exposure_layers[name].get_geometry())

    # FIXME: Use only one layer at a time for the time being
    H = hazard_data.values()[0]
    E = exposure_data.values()[0]
    attributes = impact_function.run(H, E)

    V = Vector(coordinates, projection, attributes, impact_name)
    return V
