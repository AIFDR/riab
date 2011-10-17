"""Module for piecewise constant and bilinear 2D interpolation over a rectangular mesh

This module
* is fast (base on numpy vector operations)
* depends only on numpy
* provides piecewise constant (nearest neighbour) and bilinear interpolation
* guarantees that interpolated values never exceed the four nearest neighbours
* handles missing values sensible using NaN
* is unit tested with a range of common and corner cases

"""

import numpy

def interpolate2d(x, y, A, points, mode='linear', bounds_error=False):
    """Fundamental 2D interpolation routine

    Input
        x: 1D array of x-coordinates of the mesh on which to interpolate
        y: 1D array of y-coordinates of the mesh on which to interpolate
        A: 2D array of values for each x, y pair
        points: Nx2 array of coordinates where interpolated values are sought
        mode: Determines the interpolation order. Options are
              'constant' - piecewise constant nearest neighbour interpolation
              'linear' - bilinear interpolation using the four
                         nearest neighbours (default)
        bounds_error: Boolean flag. If True (default) an exception will
                      be raised when interpolated values are requested
                      outside the domain of the input data. If False, nan
                      is returned for those values
    Output
        1D array with same length as points with interpolated values

    Notes
        Input coordinates x and y are assumed to be monotonically increasing,
        but need not be equidistantly spaced.

        A is assumed to have dimension M x N, where M = len(x) and N = len(y).
        In other words it is assumed that the x values follow the first
        (vertical) axis downwards and y values the second (horizontal) axis
        from left to right.

        If this routine is to be used for interpolation of raster grids where
        data is typically organised with longitudes (x) going from left to
        right and latitudes (y) from left to right then user
        interpolate_raster in this module

    Example:


    """

    # Input checks
    x = numpy.array(x)
    y = numpy.array(y)
    points = numpy.array(points)

    try:
        A = numpy.array(A)
        m, n = A.shape
    except Exception, e:
        msg = 'A must be a 2D numpy array: %s' % str(e)
        raise Exception(msg)

    Nx = len(x)
    Ny = len(y)
    msg = ('Input array A must have dimensions %i x %i corresponding to the '
           'lengths of the input coordinates x and y. However, '
           'A has dimensions %i x %i.' % (Nx, Ny, m, n))
    assert Nx == m, msg
    assert Ny == n, msg


    # Get interpolation points
    xi = points[:, 0]
    eta = points[:, 1]

    if bounds_error:
        msg = ('Interpolation point %f was less than the smallest value in '
               'domain %f and bounds_error was requested.' % (xi[0], x[0]))
        if xi[0] < x[0]:
            raise Exception(msg)

        msg = ('Interpolation point %f was greater than the largest value in '
               'domain %f and bounds_error was requested.' % (xi[-1], x[-1]))
        if xi[-1] > x[-1]:
            raise Exception(msg)

        msg = ('Interpolation point %f was less than the smallest value in '
               'domain %f and bounds_error was requested.' % (eta[0], y[0]))
        if eta[0] < y[0]:
            raise Exception(msg)

        msg = ('Interpolation point %f was greater than the largest value in '
               'domain %f and bounds_error was requested.' % (eta[-1], y[-1]))
        if eta[-1] > y[-1]:
            raise Exception(msg)

    # Identify elements that are outside interpolation domain
    outside = (xi < x[0]) + (eta < y[0]) + (xi > x[-1]) + (eta > y[-1])
    inside = -outside
    xi = xi[inside]
    eta = eta[inside]

    # Find upper neighbours for each interpolation point
    idx = numpy.searchsorted(x, xi)
    idy = numpy.searchsorted(y, eta)

    # Get the four neighbours for each interpolation point
    x0 = x[idx-1]
    x1 = x[idx]
    y0 = y[idy-1]
    y1 = y[idy]

    A00 = A[idx-1, idy-1]
    A01 = A[idx-1, idy]
    A10 = A[idx, idy-1]
    A11 = A[idx, idy]

    # Linear interpolation formula
    alpha = (xi - x0) / (x1 - x0)
    beta = (eta - y0) / (y1 - y0)

    Dx = A10 - A00
    Dy = A01 - A00

    Z = A00 + alpha * Dx + beta * Dy + alpha * beta * (A11 - Dx - Dy - A00)

    # Populate result with interpolated values for points inside domain
    # and NaN for values outside
    R = numpy.zeros(len(points))
    R[inside] = Z
    R[outside] = numpy.nan

    return R


def interpolate_raster(x, y, A, points, mode='linear', bounds_error=False):
    """2D interpolation of raster data

    It is assumed that data is organised in A as latitudes from
    bottom up along the first dimension and longitudes from west to east
    along the second dimension.

    Further it is assumed that x is the vector of longitudes and y the
    vector of latitudes.

    See interpolate2d for details of the interpolation routine
    """

    # Flip matrix A up-down so that scipy will interpret latitudes correctly.
    A = numpy.flipud(A)

    # Transpose A to have y coordinates along the first axis and x coordinates
    # along the second axis
    A = A.transpose()

    # Call underlying interpolation routine and return
    res = interpolate2d(x, y, A, points, mode=mode, bounds_error=bounds_error)
    return res



