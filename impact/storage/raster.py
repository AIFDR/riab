"""Class Raster
"""

import os
import numpy
from osgeo import gdal
from projection import Projection
from utilities import driver_map
from impact.engine.interpolation import interpolate_raster_vector


class Raster:
    """Internal representation of raster (coverage) data
    """

    def __init__(self, data=None, projection=None, geotransform=None, name=''):
        """Initialise object with either data or filename

        Input
            data: Either a filename of a raster file format known to GDAL
                  Or an MxN array of raster data.
                  None is also allowed.
            projection: Geospatial reference in WKT format.
                        Only used if data is provide as a numeric array,
            geotransform: GDAL geotransform (6-tuple).
                          (top left x, w-e pixel resolution, rotation,
                           top left y, rotation, n-s pixel resolution).
                          See e.g. http://www.gdal.org/gdal_tutorial.html
                          Only used if data is provide as a numeric array,
            name: Optional name for layer.
                  Only used if data is provide as a numeric array,
        """

        if data is None:
            # Instantiate empty object
            self.name = 'Empty raster layer'
            self.projection = None
            self.attributes = {}
            self.coordinates = None
            self.filename = None

            return

        if isinstance(data, basestring):
            self.read_from_file(data)
        else:
            # Assume that data is provided as an array
            # with extra keyword arguments supplying metadata

            self.data = numpy.array(data, dtype='d', copy=False)

            self.filename = None
            self.name = name

            self.projection = Projection(projection)
            self.geotransform = geotransform

            self.rows = data.shape[0]
            self.columns = data.shape[1]

            self.number_of_bands = 1

    def __len__(self):
        return len(self.data.flat)

    def get_name(self):
        return self.name

    def read_from_file(self, filename):

        # Open data file for reading
        # File must be kept open, otherwise GDAL methods segfault.
        fid = self.fid = gdal.Open(filename, gdal.GA_ReadOnly)
        if fid is None:
            msg = 'Could not open file %s' % filename
            raise Exception(msg)

        # Record raster metadata from file
        basename, ext = os.path.splitext(filename)

        # If file is ASCII, check that projection is around.
        # GDAL does not check this nicely, so it is worth an
        # error message
        if ext == '.asc':
            try:
                open(basename + '.prj')
            except IOError:
                msg = ('Projection file not found for %s. You must supply '
                       'a projection file with extension .prj' % filename)
                raise Exception(msg)

        # Always use basename without leading directories as name
        coveragename = os.path.split(basename)[-1]

        self.filename = filename
        self.name = coveragename

        self.projection = Projection(self.fid.GetProjection())
        self.geotransform = self.fid.GetGeoTransform()
        self.columns = fid.RasterXSize
        self.rows = fid.RasterYSize
        self.number_of_bands = fid.RasterCount

        # Assume that file contains all data in one band
        msg = 'Only one raster band currently allowed'
        if self.number_of_bands > 1:
                print >> sys.err, ('WARNING: Number of bands in %s are %i. '
                   'Only the first band will currently be '
                   'used.' % (filename, self.number_of_bands))

        # Get first band.
        band = self.band = fid.GetRasterBand(1)
        if band is None:
            msg = 'Could not read raster band from %s' % filename
            raise Exception(msg)

    def write_to_file(self, filename):
        """Save raster data to file

        Input
            filename: filename with extension .tif
        """

        # Check file format
        _, extension = os.path.splitext(filename)

        msg = ('Invalid file type for file %s. Only extension '
               'tif allowed.' % filename)
        assert extension == '.tif', msg
        format = driver_map[extension]

        # Get raster data
        A = self.get_data()

        # Get Dimensions. Note numpy and Gdal swap order
        N, M = A.shape

        # Create empty file
        driver = gdal.GetDriverByName(format)
        fid = driver.Create(filename, M, N, 1, gdal.GDT_Float64)
        if fid is None:
            msg = ('Gdal could not create filename %s using '
                   'format %s' % (filename, format))
            raise Exception(msg)

        # Write metada
        fid.SetProjection(str(self.projection))
        fid.SetGeoTransform(self.geotransform)

        # Write data
        fid.GetRasterBand(1).WriteArray(A)

    def interpolate(self, X, name=None):
        """Interpolate values of this raster layer to other layer

        Input
            X: Layer object defining target
            name: Optional name of interpolated layer

        Output
            Y: Layer object with values of this raster layer interpolated to
               geometry of input layer X
        """

        if X.is_raster:
            if self.get_geotransform() != X.get_geotransform():
                # Need interpolation between grids
                msg = 'Intergrid interpolation not yet implemented'
                raise Exception(msg)
            else:
                # Rasters are aligned, no need to interpolate
                return self
        else:
            # Interpolate this raster layer to geometry of X
            return interpolate_raster_vector(self, X, name)

    def get_data(self, nan=False):
        """Get raster data as numeric array
        If keyword nan is True, nodata values will be replaced with NaN
        If keyword nan has a numeric value, that will be used for NODATA
        """

        # FIXME (Ole): Once we have the ability to use numpy.nan throughout,
        #              make that the default and name everything better

        if hasattr(self, 'data'):
            A = self.data
            assert A.shape[0] == self.rows and A.shape[1] == self.columns
        else:
            # Read from raster file
            A = self.band.ReadAsArray()

            M, N = A.shape
            msg = ('Dimensions of raster array do not match those of '
                   'raster file %s' % self.filename)
            assert M == self.rows, msg
            assert N == self.columns, msg

        if nan is False:
            pass
        else:
            if nan is True:
                NAN = numpy.nan
            else:
                NAN = nan

            # Replace NODATA_VALUE with NaN
            nodata = self.get_nodata_value()

            NaN = numpy.ones(A.shape, A.dtype) * NAN
            A = numpy.where(A == nodata, NaN, A)

        return A

    def get_projection(self, proj4=False):
        """Return projection of this layer.
        """
        return self.projection.get_projection(proj4)

    def get_geotransform(self):
        """Return geotransform for this raster layer

        Output
        geotransform: 6 digit vector
                      (top left x, w-e pixel resolution, rotation,
                       top left y, rotation, n-s pixel resolution).

                       See e.g. http://www.gdal.org/gdal_tutorial.html
        """

        return self.geotransform

    def get_geometry(self):
        """Return longitudes and latitudes (the axes) for grid.

        Return two vectors (longitudes and latitudes) corresponding to
        grid. The values are offset by half a pixel size to correspond to
        pixel registration.

        I.e. If the grid origin (top left corner) is (105, 10) and the
        resolution is 1 degrees in each direction, then the vectors will
        take the form

        longitudes = [100.5, 101.5, ..., 109.5]
        latitudes = [0.5, 1.5, ..., 9.5]
        """

        # Get parameters for axes
        g = self.get_geotransform()

        lon_ul = g[0]  # Longitude of upper left corner
        lat_ul = g[3]  # Latitude of upper left corner
        dx = g[1]      # Longitudinal resolution
        dy = - g[5]    # Latitudinal resolution (always(?) negative)
        nx = self.columns
        ny = self.rows

        assert dx > 0
        assert dy > 0

        # Coordinates of lower left corner
        lon_ll = lon_ul
        lat_ll = lat_ul - ny * dy

        # Coordinates of upper right corner
        lon_ur = lon_ul + nx * dx
        lat_ur = lat_ul

        # Define pixel centers along each directions
        dy2 = dy / 2
        dx2 = dx / 2

        # Define longitudes and latitudes for each axes
        x = numpy.linspace(lon_ll + dx2,
                           lon_ur - dx2, nx)
        y = numpy.linspace(lat_ll + dy2,
                           lat_ul - dy2, ny)

        # Return
        return x, y

    def __mul__(self, other):
        return self.get_data() * other.get_data()

    def __add__(self, other):
        return self.get_data() + other.get_data()

    def get_extrema(self):
        """Get min and max from raster
        If raster has a nominated no_data value, this is ignored.

        Return min, max
        """

        A = self.get_data(nan=True)
        min = numpy.nanmin(A.flat[:])
        max = numpy.nanmax(A.flat[:])

        return min, max

    def get_nodata_value(self):
        """Get the internal representation of NODATA

        If the internal value is None, the standard -9999 is assumed
        """

        nodata = self.band.GetNoDataValue()

        # Use common default in case nodata was not registered in raster file
        if nodata is None:
            nodata = -9999

        return nodata

    def get_bins(self, N=10, quantiles=False):
        """Get N values between the min and the max occurred in this dataset.

        Return sorted list of length N+1 where the first element is min and
        the last is max. Intermediate values depend on the keyword quantiles:
        If quantiles is True, they represent boundaries between quantiles.
        If quantiles is False, they represent equidistant interval boundaries.
        """

        min, max = self.get_extrema()

        levels = []
        if quantiles is False:
            # Linear intervals
            d = (max - min) / N

            for i in range(N):
                levels.append(min + i * d)
        else:
            # Quantiles
            # FIXME (Ole): Not 100% sure about this algorithm,
            # but it is close enough

            A = self.get_data(nan=True).flat[:]

            mask = numpy.logical_not(numpy.isnan(A))  # Omit NaN's
            A = A.compress(mask)

            A.sort()

            assert len(A) == A.shape[0]

            d = float(len(A) + 0.5) / N
            for i in range(N):
                levels.append(A[int(i * d)])

        levels.append(max)

        return levels

    def get_bounding_box(self):
        """Get bounding box coordinates for raster layer

        Format is [West, South, East, North]
        """

        geotransform = self.geotransform

        x_origin = geotransform[0]  # top left x
        y_origin = geotransform[3]  # top left y
        x_res = geotransform[1]     # w-e pixel resolution
        y_res = geotransform[5]     # n-s pixel resolution
        x_pix = self.columns
        y_pix = self.rows

        minx = x_origin
        maxx = x_origin + (x_pix * x_res)
        miny = y_origin + (y_pix * y_res)
        maxy = y_origin

        return [minx, miny, maxx, maxy]

    @property
    def is_raster(self):
        return True

    @property
    def is_vector(self):
        return False
