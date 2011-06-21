import os
import types
import numpy
from django.conf import settings
from impact.storage.io import get_bounding_box

TESTDATA = os.path.join(os.environ['RIAB_HOME'], 'risiko_test_data')
DEMODATA = os.path.join(os.environ['RIAB_HOME'], 'risiko_demo_data')

# Use the local GeoServer url inside GeoNode
# The ows bit at the end if VERY important because
# that is the endpoint of the OGC services.
INTERNAL_SERVER_URL = os.path.join(settings.GEOSERVER_BASE_URL, 'ows')

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

def assert_bounding_box_matches(layer, filename):
    """Verify that GeoNode layer has the same bounding box as filename
    """

    # Check integrity

    assert hasattr(layer, 'geographic_bounding_box')
    assert isinstance(layer.geographic_bounding_box, basestring)

    # Exctract bounding bounding box from layer handle
    s = 'POLYGON(('
    i = layer.geographic_bounding_box.find(s) + len(s)
    assert i > len(s)

    j = layer.geographic_bounding_box.find('))')
    assert j > i

    bbox_string = str(layer.geographic_bounding_box[i:j])
    A = numpy.array([[float(x[0]), float(x[1])] for x in
                     (p.split() for p in bbox_string.split(','))])
    south = min(A[:, 1])
    north = max(A[:, 1])
    west = min(A[:, 0])
    east = max(A[:, 0])
    bbox = [west, south, east, north]

    # Check correctness of bounding box against reference
    ref_bbox = get_bounding_box(filename)

    msg = ('Bounding box from layer handle "%s" was not as expected.\n'
           'Got %s, expected %s' % (layer.name, bbox, ref_bbox))
    assert numpy.allclose(bbox, ref_bbox, rtol=1.0e-6, atol=1.0e-8), msg


