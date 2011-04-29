"""Class Vector
"""

import os
import numpy
from osgeo import ogr
from impact.storage.projection import Projection
from impact.storage.utilities import DRIVER_MAP, TYPE_MAP


class Vector:
    """Class for abstraction of vector data
    """

    def __init__(self, data=None, projection=None, geometry=None,
                 name='Vector layer'):
        """Initialise object with either geometry or filename

        Input
            data: Can be either
                * a filename of a vector file format known to GDAL
                * List of dictionaries of fields associated with
                  point coordinates
                * None
            projection: Geospatial reference in WKT format.
                        Only used if geometry is provide as a numeric array,
            geometry: An Nx2 array of point coordinates
            name: Optional name for layer.
                  Only used if geometry is provide as a numeric array,
        """

        if data is None and projection is None and geometry is None:
            # Instantiate empty object
            self.name = name
            self.projection = None
            self.geometry = None
            self.filename = None
            self.data = None
            return

        if isinstance(data, basestring):
            self.read_from_file(data)
        else:
            # Assume that geometry is provided as an array
            # with extra keyword arguments supplying metadata

            msg = 'Geometry must be specified'
            assert geometry is not None, msg
            self.geometry = numpy.array(geometry, dtype='d', copy=False)

            msg = 'Projection must be specified'
            assert projection is not None, msg
            self.projection = Projection(projection)

            self.data = data
            self.name = name
            self.filename = None

    def __len__(self):
        return self.geometry.shape[0]

    def __eq__(self, other, rtol=1.0e-5, atol=1.0e-8):
        """Override '==' to allow comparison with other vector objecs

        Input
           other: Vector instance to compare to
           rtol, atol: Relative and absolute tolerance.
                       See numpy.allclose for details
        """

        # Check type
        if not isinstance(other, Vector):
            msg = ('Vector instance cannot be compared to %s'
                   ' as its type is %s ' % (str(other), type(other)))
            raise TypeError(msg)

        # Check projection
        if self.projection != other.projection:
            return False

        # Check geometry
        if not numpy.allclose(self.get_geometry(),
                              other.get_geometry(),
                              rtol=rtol, atol=atol):
            return False

        # Check data
        # FIXME (Ole): Rewrite when issue #65 is done
        # FIXME: Also check that keys match exactly.
        x = self.get_data()
        y = other.get_data()
        for i, a in enumerate(x):
            for key in a:
                if a[key] != y[i][key]:
                    # Not equal, try numerical comparison

                    if not numpy.allclose(a[key], y[i][key],
                                          rtol=rtol, atol=atol):
                        return False

        # Vector layers are identical up to the specified tolerance
        return True

    def __ne__(self, other):
        """Override '!=' to allow comparison with other projection objecs
        """
        return not self == other

    def get_name(self):
        return self.name

    def read_from_file(self, filename):
        """ Read and unpack vector data.

        It is assumed that the file contains only one layer with the
        pertinent features. Further it is assumed for the moment that
        all geometries are points.

        * A feature is a geometry and a set of attributes.
        * A geometry refers to location and can be point, line, polygon or
          combinations thereof.
        * The attributes or obtained through GetField()

        The full OGR architecture is documented at
        * http://www.gdal.org/ogr/ogr_arch.html
        * http://www.gdal.org/ogr/ogr_apitut.html

        Examples are at
        * danieljlewis.org/files/2010/09/basicpythonmap.pdf
        * http://invisibleroads.com/tutorials/gdal-shapefile-points-save.html
        * http://www.packtpub.com/article/geospatial-data-python-geometry
        """

        self.name, _ = os.path.splitext(filename)

        fid = ogr.Open(filename)
        if fid is None:
            msg = 'Could not open %s' % filename
            raise IOError(msg)

        # Assume that file contains all data in one layer
        msg = 'Only one vector layer currently allowed'
        if fid.GetLayerCount() > 1:
            msg = ('WARNING: Number of layers in %s are %i. '
                   'Only the first layer will currently be '
                   'used.' % (filename, fid.GetLayerCount()))
            raise Exception(msg)

        layer = fid.GetLayerByIndex(0)

        # Get spatial extent
        self.extent = layer.GetExtent()

        # Get projection
        p = layer.GetSpatialRef()
        self.projection = Projection(p)

        # Get number of features
        N = layer.GetFeatureCount()

        # Extract coordinates and attributes for all features
        geometry = []
        data = []
        for i in range(N):
            feature = layer.GetFeature(i)
            if feature is None:
                msg = 'Could not get feature %i from %s' % (i, filename)
                raise Exception(msg)

            # Record coordinates
            G = feature.GetGeometryRef()
            if G is not None and G.GetGeometryType() == ogr.wkbPoint:
                # Longitude, Latitude
                geometry.append((G.GetX(), G.GetY()))
            else:
                msg = ('Only point geometries are supported. '
                       'Geometry in filename %s '
                       'was %s.' % (filename,
                                    G.GetGeometryType()))
                raise Exception(msg)

            # Record attributes by name
            number_of_fields = feature.GetFieldCount()
            fields = {}
            for j in range(number_of_fields):
                name = feature.GetFieldDefnRef(j).GetName()
                fields[name] = feature.GetField(j)
                #print 'Field (name: value) = (%s: %s)' % (name, fields[name])

            data.append(fields)

        self.geometry = numpy.array(geometry, dtype='d', copy=False)
        self.data = data
        self.filename = filename

    def write_to_file(self, filename):
        """Save vector data to file

        Input
            filename: filename with extension .shp or .gml
        """

        # Derive layername from filename (excluding preceding dirs)
        x = os.path.split(filename)[-1]
        layername, extension = os.path.splitext(x)

        # Check file format
        msg = ('Invalid file type for file %s. Only extensions '
               'shp or gml allowed.' % filename)
        assert extension == '.shp' or extension == '.gml', msg
        driver = DRIVER_MAP[extension]

        # FIXME (Ole): Tempory flagging of GML issue
        if extension == '.gml':
            msg = ('OGR GML driver does not store geospatial reference.'
                   'This format is disabled for the time being')
            raise Exception(msg)

        # Get vector data
        geometry = self.get_geometry()
        data = self.get_data()
        N = len(geometry)

        # Clear any previous file of this name (ogr does not overwrite)
        try:
            os.remove(filename)
        except:
            pass

        # Create new file with one layer
        drv = ogr.GetDriverByName(driver)
        if drv is None:
            msg = 'OGR driver %s not available' % driver
            raise Exception(msg)

        ds = drv.CreateDataSource(filename)
        if ds is None:
            msg = 'Creation of output file %s failed' % filename
            raise Exception(msg)

        lyr = ds.CreateLayer(layername,
                             self.projection.spatial_reference,
                             ogr.wkbPoint)
        if lyr is None:
            msg = 'Could not create layer %s' % layername
            raise Exception(msg)

        # Define attributes if any
        store_attributes = False
        if data is not None:
            if len(data) > 0:
                try:
                    fields = data[0].keys()
                except:
                    msg = ('Input parameter "attributes" was specified '
                           'but it does not contain dictionaries with '
                           'field information as expected. The first'
                           'element is %s' % data[0])
                    raise Exception(msg)
                else:
                    # Establish OGR types for each element
                    ogrtypes = {}
                    for name in fields:
                        py_type = type(data[0][name])
                        ogrtypes[name] = TYPE_MAP[py_type]

            else:
                msg = ('Input parameter "data" was specified '
                       'but appears to be empty')
                raise Exception(msg)

            # Create attribute fields in layer
            store_attributes = True
            for name in fields:

                fd = ogr.FieldDefn(name, ogrtypes[name])

                # FIXME (Ole): Trying to address issue #16
                #              But it doesn't work and
                #              somehow changes the values of MMI in test
                #width = max(128, len(name))
                #print name, width
                #fd.SetWidth(width)

                if lyr.CreateField(fd) != 0:
                    msg = 'Could not create field %s' % name
                    raise Exception(msg)

        # Store point data
        for i in range(N):
            # FIXME (Ole): Need to assign entire vector if at all possible

            # Coordinates
            x = float(geometry[i, 0])
            y = float(geometry[i, 1])

            pt = ogr.Geometry(ogr.wkbPoint)
            pt.SetPoint_2D(0, x, y)

            feature = ogr.Feature(lyr.GetLayerDefn())
            feature.SetGeometry(pt)

            G = feature.GetGeometryRef()
            if G is None:
                msg = 'Could not create GeometryRef for file %s' % filename
                raise Exception(msg)

            # Attributes
            if store_attributes:
                for name in fields:
                    feature.SetField(name, data[i][name])

            # Save this feature
            if lyr.CreateFeature(feature) != 0:
                msg = 'Failed to create feature %i in file %s' % (i, filename)
                raise Exception(msg)

            feature.Destroy()

    def get_data(self):
        """Get vector data as list of attributes

        Output is a list of same length as that returned by get_geometry().
        Each entry is a dictionary of attributes for one feature.

        Entries in get_geometry() and get_data() are related as 1-to-1
        """
        if hasattr(self, 'data'):
            return self.data
        else:
            msg = 'Vector data instance does not have any attributes'
            raise Exception(msg)

    def get_geometry(self):
        """Return geometry for vector layer.

        Depending on the feature type, geometry is

        geometry type     output type
        -----------------------------
        point             coordinates (Nx2 array of longitudes and latitudes)
        line              TODO
        polygon           TODO

        """
        return self.geometry

    def get_projection(self, proj4=False):
        """Return projection of this layer as a string
        """
        return self.projection.get_projection(proj4)

    def get_bounding_box(self):
        """Get bounding box coordinates for vector layer.

        Format is [West, South, East, North]
        """
        e = self.extent
        return [e[0],  # West
                e[2],  # South
                e[1],  # East
                e[3]]  # North

    def get_extrema(self, attribute=None):
        """Get min and max values from specified attribute

        Return min, max
        """

        if attribute is None:
            msg = ('Valid attribute name must be specified in get_extrema '
                   'for vector layers. I got None.')
            raise RuntimeError(msg)

        data = self.get_data()

        msg = ('Specified attribute %s does not exist in vector layer %s. '
               'Available attributes are: '
               '%s' % (attribute, self.name, data[0].keys()))
        assert attribute in data[0], msg

        x = [a[attribute] for a in data]
        return min(x), max(x)

    def get_topN(self, attribute, N=10):
        """Get top N features

        Input
            attribute: The name of attribute where values are sought
            N: How many

        Output
            layer: New vector layer with selected features
        """

        # FIXME (Ole): Maybe generalise this to arbitrary expressions

        # Input checks
        msg = 'N must be a positive number. I got %i' % N
        assert N > 0, msg

        msg = 'Specified attribute was empty'
        assert len(attribute) > 0, msg

        msg = ('Requested attribute "%s" does not exist in vector layer '
               ' with data: %s' % (attribute,
                                         self.data[0].keys()))
        assert attribute in self.data[0], msg

        # Create list of values for specified attribute
        values = [x[attribute] for x in self.data]

        # Sort and select using Schwarzian transform
        A = zip(values, self.data, self.geometry)
        A.sort()

        # Pick top N and unpack
        _, data, geometry = zip(*A[-N:])

        # Create new Vector instance and return
        return Vector(data=data,
                      projection=self.get_projection(),
                      geometry=geometry)

    def interpolate(self, X, name=None):
        """Interpolate values of this vector layer to other layer

        Input
            X: Layer object defining target
            name: Optional name of interpolated layer

        Output
            Y: Layer object with values of this vector layer interpolated to
               geometry of input layer X
        """

        msg = 'Interpolation from vector layers not yet implemented'
        raise Exception(msg)

    @property
    def is_raster(self):
        return False

    @property
    def is_vector(self):
        return True
