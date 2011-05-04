"""
Basic plugin framework based on::
http://martyalchin.com/2008/jan/10/simple-plugin-framework/
"""

# FIXME (Ole): Surely we can do better than this.
# What if a new hazard category appears?
# It took me over one hour to find this
from impact.plugins.earthquake import *
from impact.plugins.tsunami import *
from impact.plugins.flood import *
from impact.plugins.tephra import *
from impact.plugins.core import FunctionProvider
from impact.plugins.core import get_plugins
from impact.plugins.core import compatible_layers
