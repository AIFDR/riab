import os
import unittest

from geonode.maps.utils import upload, file_upload, GeoNodeException

from impact.views import calculate
from impact.plugins.core import FunctionProvider
from impact.plugins.core import requirements_collect
from impact.plugins.core import requirement_check
from impact.plugins.core import get_plugins

from impact import storage, plugins, engine
from impact.models import Calculation, Workspace

from django.test.client import Client
from django.conf import settings
from django.utils import simplejson as json

internal_server = os.path.join(settings.GEOSERVER_BASE_URL, 'ows')

import warnings


class BasicFunction(FunctionProvider):
    """Risk plugin for testing

    :author Allen
    :rating 1
    :param requires category=="hazard"
    """

    @staticmethod
    def run(H, E,
            a=0.97429, b=11.037):

        return None


class Test_plugins(unittest.TestCase):
    """Tests of Risiko calculations
    """

    def test_get_plugins(self):
        """Getting the plugins
        """

        plugin_list = get_plugins()
        assert(len(plugin_list) > 0)

        # Check that every plugin has a requires line
        for plugin in plugin_list.values():
            requirements = requirements_collect(plugin)
            msg = 'Should be more than 1 plugin'
            assert(len(requirements) > 0), msg

            for req_str in requirements:
                msg = 'All plugins should return True or False'
                assert(requirement_check({'category': 'hazard',
                                          'subcategory': 'earthquake',
                                          'layerType': 'raster'},
                                         req_str) in [True, False]), msg

    def test_requirements_check(self):
        """Plugin requirements"""

        plugin_list = get_plugins('BasicFunction')
        assert(len(plugin_list) == 1)

        requirements = requirements_collect(plugin_list[0].values()[0])
        msg = 'Requirements are %s' % requirements
        assert(len(requirements) == 1), msg
        for req_str in requirements:
            msg = 'Should eval to True'
            assert(requirement_check({'category': 'hazard'},
                                     req_str) is True), msg
            msg = 'Should eval to False'
            assert(requirement_check({'broke': 'broke'},
                                     req_str) is False), msg

        try:
            plugin_list = get_plugins('NotRegistered')
        except AssertionError:
            pass
        else:
            assert False, 'Search should fail'

    def test_plugin_compatability(self):
        """Performance of the default plugins using internal GeoServer
        """

        plugin_list = get_plugins()
        assert(len(plugin_list) > 0)

        geoserver = {'url': settings.GEOSERVER_BASE_URL + 'ows',
                     'name': 'Local Geoserver',
                     'version': '1.0.0',
                     'id': 0}
        layers = storage.get_layers_metadata(geoserver['url'],
                                             geoserver['version'])

        msg = 'Should > 1 layer in test geoserver'
        assert(len(layers) > 0), msg

        annotated_plugins = [{'name': name,
                              'doc': f.__doc__,
                              'layers': plugins.compatible_layers(f, layers)}
                             for name, f in plugin_list.items()]

        for v in annotated_plugins:
            msg = 'layers for %s are empty' % v['name']
            assert(len(v['layers']) > 0), msg
#        print str(annotated_plugins)

    def test_django_plugins(self):
        """Django plugin functions can be retrieved correctly
        """

        # This is to get rid of Deprecation Warning in
        # low level Django module
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            c = Client()
            rv = c.post('/api/v1/functions/', data={})

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        #assert 'hazard_layer' in data.keys()
        #assert 'exposure_layer' in data.keys()
        #assert 'run_duration' in data.keys()
        #assert 'run_date' in data.keys()
        #assert 'layer' in data.keys()

    def test_plugin_calculations(self):
        """Test the calculations"""
        pass


if __name__ == '__main__':
    import logging
    os.environ["DJANGO_SETTINGS_MODULE"] = "risiko.settings"

    # Set up logging
    for _module in ['geonode.maps.utils']:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler())
        # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        _logger.setLevel(logging.CRITICAL)

    suite = unittest.makeSuite(Test_plugins, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
