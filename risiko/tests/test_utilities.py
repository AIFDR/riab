import os
import unittest
from geonode.maps.utils import batch_upload
from impact.storage.io import metadata
from django.conf import settings

TEST_DATA=os.path.join(os.environ['RIAB_HOME'], 'riab_data', 'risiko_demo_data')


class Test_utilities(unittest.TestCase):
    """Tests riab_geonode utilities
    """

    def setUp(self):
        self.datadir = TEST_DATA


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
    import logging

    os.environ["DJANGO_SETTINGS_MODULE"] = "risiko.settings"

    # Set up logging
    for _module in ['geonode.maps.utils']:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler())
        # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        _logger.setLevel(logging.DEBUG)

    suite = unittest.makeSuite(Test_utilities, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
