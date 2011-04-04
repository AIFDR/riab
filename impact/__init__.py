"""Risk In a Box."""

# Expose public functionality
from riab_server.core.engine import calculate_impact, interpolate
from riab_server.core.io import read_layer, write_coverage, \
    write_point_data
from riab_server.core.utilities import unique_filename
from riab_server.core.interpolation import raster_spline
from riab_server.function.plugins import FunctionProvider, get_function

# Import sample functions, this will cause them to be registered
# autmatically when the user does 'import riab'
from riab_server.function import sample

# Define package meta data
VERSION = (0, 0, 1)

__version__ = '.'.join(map(str, VERSION[0:3])) + ''.join(VERSION[3:])
__author__ = 'Ole Nielsen, Ted Dunstone, Ariel Nunez'
__contact__ = 'Ole.Moller.Nielsen@gmail.com'
__homepage__ = 'http://example.com'
__docformat__ = 'restructuredtext'
__license__ = 'GPL'
