import os
import unittest
from geonode.maps.utils import upload
from geonode.maps.models import Layer
from impact.storage.io import metadata
from django.conf import settings
import urllib2


TEST_DATA=os.path.join(os.environ['RIAB_HOME'], 'riab_data', 'risiko_demo_data')

def get_web_page(url, username=None, password=None):
    """Get url page possible with username and password
    """

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
    except urllib2.URLError, e:
        msg = 'Could not open URL "%s": %s' % (url, e)
        raise urllib2.URLError(msg)
    else:
        page = pagehandle.readlines()

    return page


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

        uploaded = upload(datadir)

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

            layer_name=layers[layer]

            # Check the layer is in the Django database
            Layer.objects.get(name=layer_name)      

            # Check that layer is in geoserver
            found = False
            gs_username, gs_password = settings.GEOSERVER_CREDENTIALS
    	    page = get_web_page(os.path.join(settings.GEOSERVER_BASE_URL, 'rest/layers'),
                                     username=gs_username,
                                     password=gs_password)
            for line in page:
                if line.find('rest/layers/%s.html' % layer_name) > 0:
                    found = True
            if not found:
                msg = ('Upload could not be verified, the layer %s is not '
                   'in geoserver %s, but GeoNode did not raise any errors, '
                   'this should never happen.' % (layer_name, settings.GEOSERVER_BASE_URL))
                raise GeoNodeException(msg)


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
