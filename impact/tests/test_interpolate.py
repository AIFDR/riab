import unittest
import numpy

from impact.engine.interpolation2d import interpolate2d, interpolate_raster

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

        # Define ny by nx array with values corresponding to each value of x and y
        A = numpy.zeros((len(x), len(y)))

        # Define values for each x, y pair as a linear function
        for i in range(len(x)):
            for j in range(len(y)):
                A[i, j] = linear_function(x[i], y[j])

        # Test first that original points are reproduced correctly
        for i, xi in enumerate(x):
            for j, eta in enumerate(y):
                val = interpolate2d(x, y, A, [xi], [eta], mode='linear')[0]
                ref = linear_function(xi, eta)
                assert numpy.allclose(val, ref, rtol=1e-12, atol=1e-12)

        # Then test that genuinly interpolated points are correct
        xis = numpy.linspace(x[0], x[-1], 10)
        etas = numpy.linspace(y[0], y[-1], 10)
        vals = interpolate2d(x, y, A, xis, etas, mode='linear')
        refs = linear_function(xis, etas)
        assert numpy.allclose(vals, refs, rtol=1e-12, atol=1e-12)


    def test_linear_interpolation_range(self):
        """Interpolation library works for linear function - a range of cases
        """

        for x in [[1.0, 2.0, 4.0], [-20, -19, 0], numpy.arange(200)+1000]:
            for y in [[5.0, 9.0], [100, 200, 10000]]:

                # Define ny by nx array with values corresponding to each value of x and y
                A = numpy.zeros((len(x), len(y)))

                # Define values for each x, y pair as a linear function
                for i in range(len(x)):
                    for j in range(len(y)):
                        A[i, j] = linear_function(x[i], y[j])

                # Test that linearly interpolated points are correct
                xis = numpy.linspace(x[0], x[-1], 100)
                etas = numpy.linspace(y[0], y[-1], 100)
                vals = interpolate2d(x, y, A, xis, etas, mode='linear')
                refs = linear_function(xis, etas)
                assert numpy.allclose(vals, refs, rtol=1e-12, atol=1e-12)



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
        vals = interpolate_raster(longitudes, latitudes, A, xis, etas, mode='linear')
        refs = linear_function(xis, etas)#, xis)

        assert numpy.allclose(vals, refs, rtol=1e-12, atol=1e-12)


if __name__ == '__main__':
    suite = unittest.makeSuite(Test_interpolate, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


