import os
import unittest
import warnings

from geonode.maps.utils import upload, file_upload, GeoNodeException

from impact.views import calculate
from impact.plugins.core import FunctionProvider
from impact.plugins.core import requirements_collect
from impact.plugins.core import requirement_check
from impact.plugins.core import get_plugins
from impact.plugins.core import compatible_layers

from impact.storage.utilities import get_layers_metadata

from impact.models import Calculation, Workspace

from impact.storage.io import save_to_geonode, check_layer
from impact.tests.utilities import TESTDATA
from django.test.client import Client
from django.conf import settings
from django.utils import simplejson as json
from geonode.maps.utils import get_valid_user


# FIXME (Ole): Change H, E to layers.
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

    def setUp(self):
        """Create valid superuser
        """
        self.user = get_valid_user()

    def test_get_plugins(self):
        """Plugins can be collected
        """

        plugin_list = get_plugins()
        assert(len(plugin_list) > 0)

        # Check that every plugin has a requires line
        for plugin in plugin_list.values():
            requirements = requirements_collect(plugin)
            msg = 'There were no requirements in plugin %s' % plugin
            assert(len(requirements) > 0), msg

            for req_str in requirements:
                msg = 'All plugins should return True or False'
                assert(requirement_check({'category': 'hazard',
                                          'subcategory': 'earthquake',
                                          'layerType': 'raster'},
                                         req_str) in [True, False]), msg

    def test_requirements_check(self):
        """Plugins are correctly filtered based on requirements"""

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
            msg = 'Search should fail'
            raise Exception(msg)

    def test_plugin_compatability(self):
        """Performance of the default plugins using internal GeoServer
        """

        # Upload a raster and a vector data set
        hazard_filename = os.path.join(TESTDATA,
                                       'shakemap_padang_20090930.asc')
        hazard_layer = save_to_geonode(hazard_filename)
        check_layer(hazard_layer, full=True)

        exposure_filename = os.path.join(TESTDATA,
                                         'lembang_schools.shp')
        exposure_layer = save_to_geonode(exposure_filename)
        check_layer(exposure_layer, full=True)

        # Test
        plugin_list = get_plugins()
        assert len(plugin_list) > 0

        geoserver = {'url': settings.GEOSERVER_BASE_URL + 'ows',
                     'name': 'Local Geoserver',
                     'version': '1.0.0',
                     'id': 0}
        layers = get_layers_metadata(geoserver['url'],
                                     geoserver['version'])

        msg = 'There were no layers in test geoserver'
        assert len(layers) > 0, msg

        annotated_plugins = [{'name': name,
                              'doc': f.__doc__,
                              'layers': compatible_layers(f, layers)}
                             for name, f in plugin_list.items()]

        msg = 'No compatible layers returned'
        assert len(annotated_plugins) > 0, msg

    def test_django_plugins(self):
        """Django plugin functions can be retrieved correctly
        """

        c = Client()
        rv = c.post('/impact/api/functions/', data={})

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)

    def test_plugin_selection(self):
        """Verify the plugins can recognize compatible layers.
        """
        # Upload a raster and a vector data set
        hazard_filename = os.path.join(TESTDATA,
                                       'Earthquake_Ground_Shaking.asc')
        hazard_layer = save_to_geonode(hazard_filename,
                                       user=self.user,
                                       overwrite=True)
        check_layer(hazard_layer, full=True)

        msg = 'No keywords found in layer %s' % hazard_layer.name
        assert len(hazard_layer.keywords) > 0, msg

        exposure_filename = os.path.join(TESTDATA,
                                         'lembang_schools.shp')
        exposure_layer = save_to_geonode(exposure_filename)
        check_layer(exposure_layer, full=True)
        msg = 'No keywords found in layer %s' % exposure_layer.name
        assert len(exposure_layer.keywords) > 0, msg

        c = Client()
        rv = c.post('/impact/api/functions/', data={})

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)

        assert 'functions' in data

        functions = data['functions']

        # FIXME (Ariel): This test should implement an alternative function to
        # parse the requirements, but for now it will just take the buildings
        # damage one.
        for function in functions:
            if function['name'] == 'Earthquake Building Damage Function':
                layers = function['layers']

                msg_tmpl = 'Expected layer %s in list of compatible layers: %s'

                hazard_msg = msg_tmpl % (hazard_layer.typename, layers)
                assert hazard_layer.typename in layers, hazard_msg

                exposure_msg = msg_tmpl % (exposure_layer.typename, layers)
                assert exposure_layer.typename in layers, exposure_msg

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'

    suite = unittest.makeSuite(Test_plugins, 'test_plugin_selection')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
