"""Class Vector
"""

import os
import numpy
from osgeo import ogr
from projection import Projection
from utilities import driver_map, type_map


class Vector:

    def __init__(self, attributes=None, projection=None, geometry=None,
                 name=''):
        """Initialise object with either geometry or filename

        Input
            geometry: Either a filename of a vector file format known to GDAL
                  Or an Nx2 array of point coordinates
                  None is also allowed.
            projection: Geospatial reference in WKT format.
                        Only used if geometry is provide as a numeric array,
            attributes: List of dictionaries of fields associated with
                        point coordinates.
                        None is allowed.
            name: Optional name for layer.
                  Only used if geometry is provide as a numeric array,
        """

        if geometry is None:
            # Instantiate empty object
            self.name = 'Empty vector layer'
            self.projection = None
            self.geometry = None
            self.filename = None

            return

        if isinstance(geometry, basestring):
            self.read_from_file(geometry)
        else:
            # Assume that geometry is provided as an array
            # with extra keyword arguments supplying metadata

            self.geometry = numpy.array(geometry, dtype='d', copy=False)

            self.filename = None
            self.name = name

            self.projection = Projection(projection)
            self.attributes = attributes

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
        coordinates = []
        attributes = []
        for i in range(N):
            feature = layer.GetFeature(i)
            if feature is None:
                msg = 'Could not get feature %i from %s' % (i, filename)
                raise Exception(msg)

            # Record coordinates
            G = feature.GetGeometryRef()
            if G is not None and G.GetGeometryType() == ogr.wkbPoint:
                # Longitude, Latitude
                coordinates.append((G.GetX(), G.GetY()))
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

            attributes.append(fields)

        self.geometry = numpy.array(coordinates, dtype='d', copy=False)
        self.attributes = attributes
        self.filename = filename

    def write_to_file(self, filename):
        """Save vector data to file

        Input
            filename: filename with extension .shp or .gml
        """

        # Check file format
        _, extension = os.path.splitext(filename)

        msg = ('Invalid file type for file %s - only extension '
               'shp or gml allowed.' % filename)
        assert extension in ['.shp', '.gml'], msg
        format = driver_map[extension]

        # FIXME (Ole): Tempory flagging of GML issue
        if extension == '.gml':
            msg = ('OGR GML driver does not store geospatial reference.'
                   'This format is disabled for the time being')
            raise Exception(msg)

        # Get vector data
        coordinates = self.get_geometry()
        attributes = self.get_data()

        # Input checks
        N = coordinates.shape[0]

        msg = ('Input parameter "coordinates" must be of dimension Nx2. '
               'I got %i for the second dimension' % coordinates.shape[1])
        assert coordinates.shape[1] == 2, msg

        if attributes is not None:
            msg = ('Input parameter "attributes" must either be None or have '
                   'the same number of entries "coordinates". '
                   'I got %i entries '
                   'but %i coordinates.' % (len(attributes), N))
            assert len(attributes) == N, msg

        # Derive layername from filename (excluding preceding dirs)
        # and check file format
        x = os.path.split(filename)[-1]
        layername, extension = os.path.splitext(x)

        msg = ('Invalid file type for file %s. Only extensions '
               'shp or gml allowed.' % filename)
        assert extension == '.shp' or extension == '.gml', msg
        format = driver_map[extension]

        # Clear any previous file of this name (ogr does not overwrite)
        try:
            os.remove(filename)
        except:
            pass

        # Create new file with one layer
        drv = ogr.GetDriverByName(format)
        if drv is None:
            msg = 'OGR driver %s not available' % format
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
        if attributes is not None:
            if len(attributes) > 0:
                try:
                    fields = attributes[0].keys()
                except:
                    msg = ('Input parameter "attributes" was specified '
                           'but it does not contain dictionaries with '
                           'field information as expected. The first'
                           'element is %s' % attributes[0])
                    raise Exception(msg)
                else:
                    # Establish OGR types for each element
                    ogrtypes = {}
                    for name in fields:
                        py_type = type(attributes[0][name])
                        ogrtypes[name] = type_map[py_type]

            else:
                msg = ('Input parameter "attributes" was specified '
                       'but appears to be empty')
                raise Exception(msg)

            # Create attribute fields in layer
            store_attributes = True
            for name in fields:

                fd = ogr.FieldDefn(name, ogrtypes[name])

                # FIXME (Ole): Trying to address issue #1
                #              But it doesn't work and
                #              somehow changes the values of MMI in test
                #width = max(128, len(name))
                #print name, width
                #fd.SetWidth(width)

                if lyr.CreateField(fd) != 0:
                    msg = 'Could not create field %s' % name
                    raise Exception(msg)

        # Store data
        for i in range(N):
            # FIXME (Ole): Need to assign entire vector if at all possible

            # Coordinates
            x = float(coordinates[i, 0])
            y = float(coordinates[i, 1])

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
                    feature.SetField(name, attributes[i][name])

            # Save this feature
            if lyr.CreateFeature(feature) != 0:
                msg = 'Failed to create feature %i in file %s' % (i, filename)
                raise Exception(msg)

            feature.Destroy()

    def get_data(self, nan=False):
        """Get vector data as list of attributes

        Output is a list of same length as that returned by get_geometry().
        Each entry is a dictionary of attributes for one feature.

        Entries in get_geometry() and get_data() are related as 1-to-1

        # FIXME: Not yet considered here
        (If keyword nan is True, nodata values will be replaced with NaN)
        """

        if hasattr(self, 'attributes'):
            return self.attributes
        else:
            msg = 'Vector data instance does not have attributes'
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

        attributes = self.get_data()

        msg = ('Specified attribute %s does not exist in vector layer %s. '
               'Available attributes are: '
               '%s' % (attribute, self.name, attributes[0].keys()))
        assert attribute in attributes[0], msg

        x = [a[attribute] for a in attributes]
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
               ' with attributes: %s' % (attribute,
                                         self.attributes[0].keys()))
        assert attribute in self.attributes[0], msg

        # Create list of values for specified attribute
        values = [x[attribute] for x in self.attributes]

        # Sort and select using Schwarzian transform
        A = zip(values, self.attributes, self.geometry)
        A.sort()

        # Pick top N and unpack
        _, attributes, coordinates = zip(*A[-N:])

        # Create new Vector instance and return
        return Vector(geometry=coordinates, attributes=attributes,
                      projection=self.get_projection())

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
