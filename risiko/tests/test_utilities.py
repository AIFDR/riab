import unittest
import numpy
import os

data_server_url = '203.77.224.75/riab/'
test_data = 'RISIKO_test_data.tgz'

os.environ["DJANGO_SETTINGS_MODULE"] = "riab.settings"


import sys, os, string, os
from riab import utilities
from geonode.maps.models import Layer
from riab_server.webapi.storage import metadata, login
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
            # Fetch example data
        if not os.path.exists(os.path.join('/tmp', test_data)):
            cmd = 'cd /tmp; wget -c %s' % os.path.join(data_server_url, test_data)
            os.system(cmd)

            cmd = 'cd /tmp; tar xvfz %s' % test_data
            os.system(cmd)

    def tearDown(self):
        pass

    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """

        basename, _ = os.path.splitext(test_data)
        datadir = os.path.join('/tmp', basename)
        for subdir in os.listdir(datadir):
            subdir = os.path.join(datadir, subdir)

            if os.path.isdir(subdir):

                for filename in os.listdir(subdir):

                    basename, extension = os.path.splitext(filename)

                    if extension in ['.asc', '.txt', '.tif', '.shp', '.zip']:
                        layer = utilities.file_upload('%s/%s' % (subdir, filename),
                                                           title=basename)
                        msg = ('The name of the upload file is %s' % layer.name)

                        # Verify the layer was saved:
                        saved_layer = Layer.objects.get(name=layer.name)

                        # Check the layer is in the geonode server by accessing it's url

                        # Check the layer is in the geoserver by accessing it's url
			found = False
                        gs_username, gs_password = settings.GEOSERVER_CREDENTIALS
			page = get_web_page(os.path.join(settings.GEOSERVER_BASE_URL, 'rest/layers'),
                                                         username=gs_username,
                                                         password=gs_password)
                        for line in page:
                            if line.find('rest/layers/%s.html' % layer.name) > 0:
                                found = True

                        msg = 'Did not find layer %s in geoserver %s' % (layer.name, settings.GEOSERVER_BASE_URL)
#                        import ipdb;ipdb.set_trace()
                        assert found, msg

                        # See if the layer is added to the GeoServer catalog, either via WFS or WCS
                        layer_metadata = metadata(settings.GEOSERVER_BASE_URL + 'ows', layer.typename)


                        keywords_file = os.path.join(subdir, basename + '.keywords')
                        if os.path.exists(keywords_file):
                            f = open(keywords_file, 'r')
                            keywords = [x.strip() for x in f.readlines()]
                            for k in keywords:
                                raw_key, raw_val = k.split(':')
                                val = raw_val.strip()
                                key = raw_key.strip()
                                msg = ("Key '%s' is not in layer metadata dict for layer %s."
                                       " Present keys are: (%s)" % (key, filename, layer_metadata.keys()))
                                assert key in layer_metadata, msg
                                actual_value = layer_metadata[key].strip()
                                msg = "Expected %s but got %s" % (val, actual_value)
                                assert actual_value == val, msg

if __name__ == '__main__':


    suite = unittest.makeSuite(Test_utilities, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
