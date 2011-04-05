import unittest
import numpy
import os

data_server_url = '203.77.224.75/riab/'
test_data = 'RISIKO_test_data.tgz'

os.environ["DJANGO_SETTINGS_MODULE"] = "risiko.settings"


import sys, os, string, os
from geonode.maps.models import Layer
from geonode.maps.utils import batch_upload
from impact.storage.io import metadata
from django.conf import settings
import urllib2
import logging

# Set up logging
for _module in ['riab.utilities', 'geonode.maps.views', 'geonode.maps.gs_helpers']:
    _logger = logging.getLogger(_module)
    _logger.addHandler(logging.StreamHandler())
    # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    # The earlier a level appears in this list, the more output it will produce in the log file.
    _logger.setLevel(logging.INFO)


class Test_utilities(unittest.TestCase):
    """Tests riab_geonode utilities
    """

    def setUp(self):
            # Fetch example data
        if not os.path.exists(os.path.join('/tmp', test_data)):
            cmd = 'cd /tmp; wget -c %s' % os.path.join(data_server_url, test_data)
            os.system(cmd)

            cmd = 'cd /tmp; tar xvfz %s' % test_data
            os.system(cmd)
        self.datadir = os.path.join('/tmp', test_data)

    def tearDown(self):
        pass

    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """
        uploaded = batch_upload(self.datadir)
        for item in uploaded:
            errors = 'errors' in item
            msg = 'Could not upload %s. ' % item['file']
            assert errors == False, msg + 'Error was: %s' % item['errors']


if __name__ == '__main__':


    suite = unittest.makeSuite(Test_utilities, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
