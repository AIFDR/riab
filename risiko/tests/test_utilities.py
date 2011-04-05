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
        pass

    def tearDown(self):
        pass


    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """
        layers = {}
        expected_layers = []
        datadir = TEST_DATA

        for subdir in os.listdir(datadir):
            subdir = os.path.join(datadir, subdir)
            if os.path.isdir(subdir):
                for filename in os.listdir(subdir):
                    basename, extension = os.path.splitext(filename)
                    if extension in ['.asc', '.tif', '.shp', '.zip']:
                        expected_layers.append(os.path.join(subdir, filename))

        uploaded = batch_upload(datadir)

        for item in uploaded:
            errors = 'errors' in item
            msg = 'Could not upload %s. ' % item['file']
            assert errors is False, msg + 'Error was: %s' % item['errors']
            msg = 'Upload should have returned either "name" or "errors" for file %s.' % item['file']
            assert 'name' in item, msg
            layers[item['file']]=item['name']

        msg = ('There were %s compatible layers in the directory, but only %s '
               'were sucessfully uploaded'  % (len(expected_layers), len(layers)))
        assert len(layers) == len(expected_layers), msg
        uploaded_layers = [layer for layer in layers.items()]
        for layer in expected_layers:
            msg = ('The following file should have been uploaded but was not: %s. '
                    % layer)
            assert layer in layers, msg
        

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
