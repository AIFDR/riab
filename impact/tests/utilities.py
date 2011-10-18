import os
import time
import types
import numpy
from django.conf import settings
from impact.storage.io import download, get_bounding_box, get_metadata

TESTDATA = os.path.join(os.environ['RIAB_HOME'], 'risiko_test_data')

# Use the local GeoServer url inside GeoNode
# The ows bit at the end if VERY important because
# that is the endpoint of the OGC services.
INTERNAL_SERVER_URL = os.path.join(settings.GEOSERVER_BASE_URL, 'ows')

# Known feature counts in test data
FEATURE_COUNTS = {'lembang_schools.shp': 144,
                  'tsunami_exposure_BB.shp': 7529,
                  'kecamatan_geo.shp': 42,
                  'Padang_WGS84.shp': 3896,
                  'OSM_building_polygons_20110905.shp': 34960,
                  'OSM_subset.shp': 79}

# For testing
GEOTRANSFORMS = [(105.3000035, 0.008333, 0.0, -5.5667785, 0.0, -0.008333),
                 (105.29857, 0.0112, 0.0, -5.565233000000001, 0.0, -0.0112),
                 (96.956, 0.03074106, 0.0, 2.2894972560001, 0.0, -0.03074106)]


def _same_API(X, Y, exclude=None):
    """Check that public methods of X also exist in Y
    """

    if exclude is None:
        exclude = []

    for name in dir(X):

        # Skip internal symbols
        if name.startswith('_'):
            continue

        # Skip explicitly excluded methods
        if name in exclude:
            continue

        # Check membership of methods
        attr = getattr(X, name)
        if isinstance(attr, types.MethodType):
            if name not in dir(Y):
                msg = 'Method %s of %s was not found in %s' % (name, X, Y)
                raise Exception(msg)


def same_API(X, Y, exclude=None):
    """Check that public methods of X and Y are the same.

    Input
        X, Y: Python objects
        exclude: List of names to exclude from comparison or None
    """

    _same_API(X, Y, exclude=exclude)
    _same_API(Y, X, exclude=exclude)

    return True


def get_web_page(url, username=None, password=None):
    """Get url page possible with username and password.
    """
    import urllib2

    if username is not None:

        # Create password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        # create the handler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    try:
        pagehandle = urllib2.urlopen(url)
    except HTTPError, e:
        msg = ('The server couldn\'t fulfill the request. '
                'Error code: ' % e.code)
        e.args = (msg,)
        raise
    except urllib2.URLError, e:
        msg = 'Could not open URL "%s": %s' % (url, e)
        e.args = (msg,)
        raise
    else:
        page = pagehandle.readlines()

    return page


def centroid_formula(P):
    """Naive implementation of centroid formula

    Input
        P: Polygon


    NOTE: This is not used for anything. Also it does not normalise
          the input so is prone to rounding errors.
    """

    P = numpy.array(P)

    msg = ('Polygon is assumed to consist of coordinate pairs. '
           'I got second dimension %i instead of 2' % P.shape[1])
    assert P.shape[1] == 2, msg
    N = P.shape[0] - 1

    x = P[:, 0]
    y = P[:, 1]

    # Area: 0.5 sum_{i=0}^{N-1} (x_i y_{i+1} - x_{i+1} y_i)
    A = 0.0
    for i in range(N):
        A += x[i] * y[i + 1] - x[i + 1] * y[i]
    A = A / 2

    # Centroid: sum_{i=0}^{N-1} (x_i + x_{i+1})(x_i y_{i+1} - x_{i+1} y_i)/(6A)
    Cx = 0.0
    for i in range(N):
        Cx += (x[i] + x[i + 1]) * (x[i] * y[i + 1] - x[i + 1] * y[i])
    Cx = Cx / 6 / A

    Cy = 0.0
    for i in range(N):
        Cy += (y[i] + y[i + 1]) * (x[i] * y[i + 1] - x[i + 1] * y[i])
    Cy = Cy / 6 / A

    return [Cx, Cy]


def combine_coordinates(x, y):
    """Make list of all combinations of points for x and y coordinates
    """

    points = []
    for px in x:
        for py in y:
            points.append((px, py))
    points = numpy.array(points)

    return points


