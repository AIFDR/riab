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


def calculate_impact(hazard_level, exposure_level, impact_function,
                     comment=''):
    """Calculate impact levels as a function of hazard and exposure levels

    Input

        I.e. for the moment we take only one unnamed hazard level
        and one unnamed exposure level.

        FIXME: This is has been reverted back to single names, so the doc
        string below is not current.
        hazard_levels: A dictionary of named hazard levels,
                       {'h1': H1, 'h2': H2, ..., 'hn': Hn} where each H is a
                       filename and h is a name associated with that layer.
        exposure_levels: A dictionary of exposure levels or name of GML file
                         with exposure attributes.
        impact_function: Function of the form f(H, E) where H and E are
                         dictionaries of aligned numpy arrays named the same
                         way as the input layers
        comment:

    Output
        filename of resulting impact layer (GML). Comment is embedded as
        metadata. Filename is generated from input data and date.

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

    # FIXME: Convert single layers to dictionaries with default names.
    hazard_levels = {'hazard': hazard_level}
    exposure_levels = {'exposure': exposure_level}

    # Input checks
    check_data_integrity(hazard_levels.values() + exposure_levels.values())

    # Read hazard data
    hazard_layers = read_hazard_data(hazard_levels)

    # Read exposure data
    exposure_layers = read_exposure_data(exposure_levels)

    # Establish interpolated hazard values at points that are aligned
    # with those of the exposure layers. Exposure layers are all assumed
    # to be aligned already.
    interpolation_layer = exposure_layers.values()[0]
    interpolated_hazard_layers = {}
    for name in hazard_layers:
        hazard_layer = hazard_layers[name]
        H = interpolate(hazard_layer, interpolation_layer)
        interpolated_hazard_layers[name] = H

    # Pass hazard and exposure dictionaries to plugin
    F = call_impact_function(impact_function,
                             interpolated_hazard_layers,
                             exposure_layers,
                             name='Impact')  # FIXME: Think about this

    # Write result and return filename
    # FIXME (Ole): Maybe this filename should be defined in the plugin
    #              Oh Yes it should.

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
                coordinates = layer.get_coordinates()
            else:
                msg = ('Coordinates in input vector layers are different: '
                       '%s %s' % (coordinates, layer.get_coordinates()))
                assert numpy.allclose(coordinates,
                                      layer.get_coordinates()), msg


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


def interpolate(Source, Target, name=None):
    """Interpolate values from Source to locations in Target

    Input
        Source: Data set containing values at given locations
        Target: Data set containing locations where values form
                Source are sought
        name: Name for new attribute.
              If None (default) the name of Source is used

    Output
        Data set with values form Source interpolated to locations at Target
        It will have the same type and dimensionality as Target.
    """

    if Source.is_raster and Target.is_vector:
        return interpolate_raster_vector(Source, Target, name)

    if Source.is_raster and Target.is_raster:
        if Source.get_geotransform() == Target.get_geotransform():
            # No need to interpolate
            return Source
        else:
            # Need interpolation between grids
            msg = 'Intergrid interpolation not yet implemented'
            raise Exception(msg)

    if Source.is_vector:
        # Need interpolation from vector data
        msg = 'Interpolation from vector data not yet implemented'
        raise Exception(msg)


def interpolate_raster_vector(R, V, name=None):
    """Interpolate from raster layer to point data

    Input
        R: Raster data set (coverage)
        V: Vector data set (points)
        name: Name for new attribute.
              If None (default) the name of R is used

    Output
        I: Vector data set; points located as V with values interpolated from R

    """

    # FIXME: We probably need to rename this to interpolate_raster_vector
    #        and have another called interpolate_raster_raster and so on.

    # FIXME: I think this interpolation can do grids as well if the
    #        interpolator is called with x and y being 1D arrays (axes)

    # Input checks
    assert R.is_raster
    assert V.is_vector

    # Get raster data and corresponding x and y axes

    # FIXME (Ole): Replace NODATA with 0 until we can handle proper NaNs
    A = R.get_data(nan=0.0)
    longitudes, latitudes = R.get_geometry()
    assert len(longitudes) == A.shape[1]
    assert len(latitudes) == A.shape[0]

    # Create interpolator
    f = raster_spline(longitudes, latitudes, A)

    # Get vector points but ignore attributes
    coordinates, expected_values = V.get_data()

    # Interpolate and create new attribute
    N = len(V)
    attributes = []
    if name is None:
        name = R.get_name()

    # FIXME (Ole): Profiling may suggest that his loop should be written in C
    for i in range(N):
        xi = coordinates[i, 0]   # Longitude
        eta = coordinates[i, 1]  # Latitude

        # Use layer name from raster for new attribute
        value = float(f(xi, eta))
        attributes.append({name: value})

    return Vector(coordinates, V.get_projection(), attributes)


def call_impact_function(impact_function,
                         hazard_layers,
                         exposure_layers,
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


def call_impact_function_raster(impact_function,
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


def call_impact_function_vector(impact_function,
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
        hazard_data[name] = hazard_layers[name].get_data()
        assert hazard_layers[name].is_vector

        # SANITY
        if coordinates is None:
            coordinates = hazard_layers[name].get_coordinates()
        else:
            assert numpy.allclose(coordinates,
                                  hazard_layers[name].get_coordinates())

    exposure_data = {}
    for name in exposure_layers:
        exposure_data[name] = exposure_layers[name].get_data()
        assert exposure_layers[name].is_vector

        projection = exposure_layers[name].get_projection()

        # SANITY
        if coordinates is None:
            coordinates = exposure_layers[name].get_coordinates()
        else:
            assert numpy.allclose(coordinates,
                                  exposure_layers[name].get_coordinates())

    # FIXME: Use only one layer at a time for the time being
    H = hazard_data.values()[0]
    E = exposure_data.values()[0]
    attributes = impact_function.run(H, E)

    V = Vector(coordinates, projection, attributes, impact_name)
    return V
