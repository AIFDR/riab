"""Upload test data to GeoServer

# Data is assumed to reside in subdirectories of ./data named by their workspace.
# The standard workspace names are
# - hazard
# - exposure
# - boundaries
# - impact
# - sources
"""

data_server_url = '203.77.224.75/riab/'
test_data = 'RISIKO_test_data.tgz'


import sys, os, string, os
from riab.utilities import file_upload

if __name__ == '__main__':

    # Fetch example data
    if not os.path.exists(os.path.join('/tmp', test_data)):
        cmd = 'cd /tmp; wget %s' % os.path.join(data_server_url, test_data)
        os.system(cmd)

    cmd = 'cd /tmp; tar xvfz %s' % test_data
    os.system(cmd)

    basename, _ = os.path.splitext(test_data)
    datadir = os.path.join('/tmp', basename)

    # Upload test data and record layers for subsequent generation of Open Layers file
    for subdir in os.listdir(datadir):
        subdir = os.path.join(datadir, subdir)

        if os.path.isdir(subdir):

            for filename in os.listdir(subdir):

                basename, extension = os.path.splitext(filename)

                if extension in ['.asc', '.txt', '.tif', '.shp', '.zip']:
                    print 'Uploading %s' % filename

                    file_upload('%s/%s' % (subdir, filename), title=basename)


import logging
for _module in ["riab.utilities", "geonode.maps.gs_helpers"]:
    _logger = logging.getLogger(_module)
    _logger.addHandler(logging.StreamHandler())
    # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    # The earlier a level appears in this list, the more output it will produce in the log file.
    _logger.setLevel(logging.INFO)
