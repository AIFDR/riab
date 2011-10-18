"""Module 2D interpolation over a rectangular mesh

This module
* provides piecewise constant (nearest neighbour) and bilinear interpolation
* is fast (based on numpy vector operations)
* depends only on numpy
* guarantees that interpolated values never exceed the four nearest neighbours
* handles missing values in domain sensibly using NaN
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
    x, y, A, xi, eta = check_inputs(x, y, A, points, bounds_error)

    # Identify elements that are outside interpolation domain or NaN
    outside = (xi < x[0]) + (eta < y[0]) + (xi > x[-1]) + (eta > y[-1])
    outside += numpy.isnan(xi) + numpy.isnan(eta)

    inside = -outside
    xi = xi[inside]
    eta = eta[inside]

    # Find upper neighbours for each interpolation point
    idx = numpy.searchsorted(x, xi, side='left')
    idy = numpy.searchsorted(y, eta, side='left')

    # Internal check (index == 0 is OK)
    msg = 'Interpolation point outside domain. This should never happen. Email Ole.Moller.Nielsen@gmail.com'
    assert max(idx) < len(x), msg
    assert max(idy) < len(y), msg

    #print
    #print x[0], x[-1]
    #print xi[0], xi[-1]
    #print min(xi), max(xi)
    #print numpy.where(idx == 3)
    #print xi[numpy.where(idx == 3)]
    #print numpy.where(numpy.isnan(xi))

    #print
    #print max(x)

    # Get the four neighbours for each interpolation point
    x0 = x[idx - 1]
    x1 = x[idx]
    y0 = y[idy - 1]
    y1 = y[idy]

    A00 = A[idx - 1, idy - 1]
    A01 = A[idx - 1, idy]
    A10 = A[idx, idy - 1]
    A11 = A[idx, idy]

    # Linear interpolation formula
    alpha = (xi - x0) / (x1 - x0)
    beta = (eta - y0) / (y1 - y0)

    Dx = A10 - A00
    Dy = A01 - A00

    Z = A00 + alpha * Dx + beta * Dy + alpha * beta * (A11 - Dx - Dy - A00)

    # Self test
    mZ = numpy.nanmax(Z)
    mA = numpy.nanmax(A)
    msg = 'Internal check failed. Max interpolated value %.15f exceeds max grid value %.15f ' % (mZ, mA)
    assert mZ <= mA, msg

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


def check_inputs(x, y, A, points, bounds_error):
    """Check inputs for interpolate2d function
    """

    try:
        x = numpy.array(x)
    except Exception, e:
        msg = ('Input vector x could not be converted to numpy array: '
               '%s' % str(e))
        raise Exception(msg)

    try:
        y = numpy.array(y)
    except Exception, e:
        msg = ('Input vector y could not be converted to numpy array: '
               '%s' % str(e))
        raise Exception(msg)


    msg = ('Input vector x must be monotoneously increasing. I got min(x) == %.15f, '
           'but x[0] == %.15f' % (min(x), x[0]))
    assert min(x) == x[0], msg

    msg = ('Input vector y must be monotoneously increasing. I got min(y) == %.15f, '
           'but y[0] == %.15f' % (min(y), y[0]))
    assert min(y) == y[0], msg

    msg = ('Input vector x must be monotoneously increasing. I got max(x) == %.15f, '
           'but x[-1] == %.15f' % (max(x), x[-1]))
    assert max(x) == x[-1], msg

    msg = ('Input vector y must be monotoneously increasing. I got max(y) == %.15f, '
           'but y[-1] == %.15f' % (max(y), y[-1]))
    assert max(y) == y[-1], msg


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
    points = numpy.array(points)
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

    return x, y, A, xi, eta
