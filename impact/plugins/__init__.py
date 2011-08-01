"""
Basic plugin framework based on::
http://martyalchin.com/2008/jan/10/simple-plugin-framework/
"""

# FIXME (Ole): Surely we can do better than this.
# What if a new hazard category appears?
# It took me over one hour to find this

import os
import os.path
import glob

dirname = os.path.dirname(__file__)

## import all the subdirectories
for f in os.listdir(dirname):
	if os.path.isdir(os.path.join(dirname,f)):
		exec('from impact.plugins.%s import *'%f, locals(), globals())


from impact.plugins.core import FunctionProvider
from impact.plugins.core import get_plugins
from impact.plugins.core import compatible_layers
