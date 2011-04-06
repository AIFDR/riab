"""
Basic plugin framework based on::
http://martyalchin.com/2008/jan/10/simple-plugin-framework/
"""
from impact.plugins.earthquake import *
from impact.plugins.tsunami import *
from impact.plugins.core import FunctionProvider, get_plugins, compatible_layers
