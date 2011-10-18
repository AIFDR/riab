import unittest
import numpy

from impact.engine.interpolation2d import interpolate2d, interpolate_raster
from impact.tests.utilities import combine_coordinates
from impact.storage.utilities import nanallclose


def linear_function(x, y):
    """Auxiliary function for use with interpolation test
    """

    return x + y / 2.0


class Test_interpolate(unittest.TestCase):

    def test_linear_interpolation_basic(self):
        """Interpolation library works for linear function - basic test
        """

        # Define pixel centers along each direction
        x = [1.0, 2.0, 4.0]
        y = [5.0, 9.0]

        # Define ny by nx array with corresponding values
        A = numpy.zeros((len(x), len(y)))

        # Define values for each x, y pair as a linear function
        for i in range(len(x)):
            for j in range(len(y)):
                A[i, j] = linear_function(x[i], y[j])

        # Test first that original points are reproduced correctly
        for i, xi in enumerate(x):
            for j, eta in enumerate(y):
                val = interpolate2d(x, y, A, [(xi, eta)], mode='linear')[0]
                ref = linear_function(xi, eta)
                assert numpy.allclose(val, ref, rtol=1e-12, atol=1e-12)

        # Then test that genuinly interpolated points are correct
        xis = numpy.linspace(x[0], x[-1], 10)
        etas = numpy.linspace(y[0], y[-1], 10)
        points = combine_coordinates(xis, etas)

        vals = interpolate2d(x, y, A, points, mode='linear')
        refs = linear_function(points[:, 0], points[:, 1])
        assert numpy.allclose(vals, refs, rtol=1e-12, atol=1e-12)

    def test_linear_interpolation_range(self):
        """Interpolation library works for linear function - a range of cases
        """

        for x in [[1.0, 2.0, 4.0], [-20, -19, 0], numpy.arange(200) + 1000]:
            for y in [[5.0, 9.0], [100, 200, 10000]]:

                # Define ny by nx array with corresponding values
                A = numpy.zeros((len(x), len(y)))

                # Define values for each x, y pair as a linear function
                for i in range(len(x)):
                    for j in range(len(y)):
                        A[i, j] = linear_function(x[i], y[j])

                # Test that linearly interpolated points are correct
                xis = numpy.linspace(x[0], x[-1], 100)
                etas = numpy.linspace(y[0], y[-1], 100)
                points = combine_coordinates(xis, etas)

                vals = interpolate2d(x, y, A, points, mode='linear')
                refs = linear_function(points[:, 0], points[:, 1])
                assert numpy.allclose(vals, refs, rtol=1e-12, atol=1e-12)

    def test_linear_interpolation_nan_points(self):
        """Interpolation library works with interpolation points being NaN

        This is was the reason for bug reported in: https://github.com/AIFDR/riab/issues/155
        """

        # Define pixel centers along each direction
        x = [1.0, 2.0, 4.0]
        y = [5.0, 9.0]

        # Define ny by nx array with corresponding values
        A = numpy.zeros((len(x), len(y)))

        # Define values for each x, y pair as a linear function
        for i in range(len(x)):
            for j in range(len(y)):
                A[i, j] = linear_function(x[i], y[j])

        # Then test that interpolated points can contain NaN
        xis = numpy.linspace(x[0], x[-1], 10)
        etas = numpy.linspace(y[0], y[-1], 10)
        xis[6:7] = numpy.nan
        etas[3] = numpy.nan
        points = combine_coordinates(xis, etas)

        vals = interpolate2d(x, y, A, points, mode='linear')
        refs = linear_function(points[:, 0], points[:, 1])
        assert nanallclose(vals, refs, rtol=1e-12, atol=1e-12)


    def test_linear_interpolation_nan_array(self):
        """Interpolation library works with grid points being NaN
        """

        # Define pixel centers along each direction
        x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        y = [4.0, 5.0, 7.0, 9.0, 11.0, 13.0]

        # Define ny by nx array with corresponding values
        A = numpy.zeros((len(x), len(y)))

        # Define values for each x, y pair as a linear function
        for i in range(len(x)):
            for j in range(len(y)):
                A[i, j] = linear_function(x[i], y[j])
        A[2, 3] = numpy.nan  # (x=2.0, y=9.0): NaN

        # Then test that interpolated points can contain NaN
        xis = numpy.linspace(x[0], x[-1], 12)
        etas = numpy.linspace(y[0], y[-1], 10)
        points = combine_coordinates(xis, etas)

        vals = interpolate2d(x, y, A, points, mode='linear')
        refs = linear_function(points[:, 0], points[:, 1])

        # Set reference result with expected NaNs and compare
        for i, (xi, eta) in enumerate(points):
            if (1.0 < xi <= 3.0) and (7.0 < eta <= 11.0):
                refs[i] = numpy.nan
            #print xi, eta, refs[i], vals[i]

        assert nanallclose(vals, refs, rtol=1e-12, atol=1e-12)



    def test_linear_interpolation_outside_domain(self):
        """Interpolation library sensibly handles values outside the domain
        """

        # Define pixel centers along each direction
        x = [1.0, 2.0, 4.0]
        y = [5.0, 9.0]

        # Define ny by nx array with corresponding values
        A = numpy.zeros((len(x), len(y)))

        # Define values for each x, y pair as a linear function
        for i in range(len(x)):
            for j in range(len(y)):
                A[i, j] = linear_function(x[i], y[j])

        # Simple example first for debugging
        xis = numpy.linspace(0.9, 4.0, 4)
        etas = numpy.linspace(5, 9.1, 3)
        points = combine_coordinates(xis, etas)
        refs = linear_function(points[:, 0], points[:, 1])

        vals = interpolate2d(x, y, A, points, mode='linear',
                             bounds_error=False)
        msg = ('Length of interpolation points %i differs from length '
               'of interpolated values %i' % (len(points), len(vals)))
        assert len(points) == len(vals), msg
        for i, (xi, eta) in enumerate(points):
            if xi < x[0] or xi > x[-1] or eta < y[0] or eta > y[-1]:
                assert numpy.isnan(vals[i])
            else:
                msg = ('Got %.15f for (%f, %f), expected %.15f'
                       % (vals[i], xi, eta, refs[i]))
                assert numpy.allclose(vals[i], refs[i],
                                      rtol=1.0e-12, atol=1.0e-12), msg

        # Try a range of combinations of points outside domain
        # with error_bounds True
        for lox in [x[0], x[0] - 1]:
            for hix in [x[-1], x[-1] + 1]:
                for loy in [y[0], y[0] - 1]:
                    for hiy in [y[-1], y[-1] + 1]:

                        # Then test that points outside domain can be handled
                        xis = numpy.linspace(lox, hix, 4)
                        etas = numpy.linspace(loy, hiy, 4)
                        points = combine_coordinates(xis, etas)

                        if lox < x[0] or hix > x[-1] or \
                                loy < x[0] or hiy > y[-1]:
                            try:
                                vals = interpolate2d(x, y, A, points,
                                                     mode='linear',
                                                     bounds_error=True)
                            except Exception, e:
                                pass
                            else:
                                msg = 'Should have raise bounds error'
                                raise Exception(msg)

        # Try a range of combinations of points outside domain with
        # error_bounds False
        for lox in [x[0], x[0] - 1, x[0] - 10]:
            for hix in [x[-1], x[-1] + 1, x[-1] + 5]:
                for loy in [y[0], y[0] - 1, y[0] - 10]:
                    for hiy in [y[-1], y[-1] + 1, y[-1] + 10]:

                        # Then test that points outside domain can be handled
                        xis = numpy.linspace(lox, hix, 10)
                        etas = numpy.linspace(loy, hiy, 10)
                        points = combine_coordinates(xis, etas)
                        refs = linear_function(points[:, 0], points[:, 1])
                        vals = interpolate2d(x, y, A, points,
                                             mode='linear', bounds_error=False)

                        assert len(points) == len(vals), msg
                        for i, (xi, eta) in enumerate(points):
                            if xi < x[0] or xi > x[-1] or\
                                    eta < y[0] or eta > y[-1]:
                                msg = 'Expected NaN for %f, %f' % (xi, eta)
                                assert numpy.isnan(vals[i]), msg
                            else:
                                msg = ('Got %.15f for (%f, %f), expected '
                                       '%.15f' % (vals[i], xi, eta, refs[i]))
                                assert numpy.allclose(vals[i], refs[i],
                                                      rtol=1.0e-12,
                                                      atol=1.0e-12), msg

    def test_interpolation_raster_data(self):
        """Interpolation library works for raster data

        This shows interpolation of data arranged with
        latitudes bottom - up and
        longitudes left - right
        """

        # Create test data
        lon_ul = 100  # Longitude of upper left corner
        lat_ul = 10   # Latitude of upper left corner
        numlon = 8    # Number of longitudes
        numlat = 5    # Number of latitudes
        dlon = 1
        dlat = -1

        # Define array where latitudes are rows and longitude columns
        A = numpy.zeros((numlat, numlon))

        # Establish coordinates for lower left corner
        lat_ll = lat_ul - numlat
        lon_ll = lon_ul

        # Define pixel centers along each direction
        longitudes = numpy.linspace(lon_ll + 0.5,
                                    lon_ll + numlon - 0.5, numlon)
        latitudes = numpy.linspace(lat_ll + 0.5,
                                   lat_ll + numlat - 0.5, numlat)

        # Define raster with latitudes going bottom-up (south to north).
        # Longitudes go left-right (west to east)
        for i in range(numlat):
            for j in range(numlon):
                A[numlat - 1 - i, j] = linear_function(longitudes[j],
                                                       latitudes[i])

        # Then test that interpolated points are correct
        xis = numpy.linspace(lon_ll + 1, lon_ll + numlon - 1, 100)
        etas = numpy.linspace(lat_ll + 1, lat_ll + numlat - 1, 100)
        points = combine_coordinates(xis, etas)

        vals = interpolate_raster(longitudes, latitudes, A, points,
                                  mode='linear')
        #refs = linear_function(xis, etas)#, xis)
        refs = linear_function(points[:, 0], points[:, 1])

        assert numpy.allclose(vals, refs, rtol=1e-12, atol=1e-12)


if __name__ == '__main__':
    suite = unittest.makeSuite(Test_interpolate, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
