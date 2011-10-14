import unittest
import os
from django.test.client import Client
from django.utils import simplejson as json
from django.conf import settings
from impact.storage.io import save_to_geonode

from geonode.maps.utils import check_geonode_is_up
from geonode.maps.models import Layer
from geonode.maps.utils import get_valid_user
from impact.storage.io import check_layer
from impact.tests.utilities import TESTDATA, INTERNAL_SERVER_URL


class Test_HTTP(unittest.TestCase):
    """Test suite for API
    """

    def setUp(self):
        """Check geonode and create valid superuser
        """
        check_geonode_is_up()
        self.user = get_valid_user()

    def tearDown(self):
        pass

    def test_functions(self):
        """Functions can be retrieved from the HTTP Rest API
        """

        c = Client()
        rv = c.get('/impact/api/functions/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)

        msg = ('The api should return a dictionary with at least one item. '
               'The key of that item should be "functions"')
        assert 'functions' in data, msg
        functions = data['functions']

        msg = ('No functions were found in the functions list, '
               'not even the built-in ones')
        assert len(functions) > 0, msg

    def test_layers(self):
        """Layers can be retrieved from the HTTP Rest API
        """

        c = Client()
        rv = c.get('/impact/api/layers/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)

    def test_calculate_fatality(self):
        """Earthquake fatalities calculation via the HTTP Rest API is correct
        """

        # Upload required data first
        for filename in ['Earthquake_Ground_Shaking.asc',
                         'Population_2010_clip.tif']:
            thefile = os.path.join(TESTDATA, filename)
            uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)
            check_layer(uploaded, full=True)

        # Run calculation through API
        c = Client()
        rv = c.post('/impact/api/calculate/',
                    dict(hazard_server=INTERNAL_SERVER_URL,
                         hazard='geonode:earthquake_ground_shaking',
                         exposure='geonode:population_2010_clip',
                         exposure_server=INTERNAL_SERVER_URL,
                         bbox='99.36,-2.199,102.237,0.00',
                         impact_function='Earthquake Fatality Function',
                         keywords='test,earthquake,fatality'))

        msg = 'Expected status code 200, got %i' % rv.status_code
        self.assertEqual(rv.status_code, 200), msg

        msg = ('Expected Content-Type "application/json", '
               'got %s' % rv['Content-Type'])
        self.assertEqual(rv['Content-Type'], 'application/json'), msg

        data = json.loads(rv.content)

        if data['stacktrace'] is not None:
            msg = data['stacktrace']
            raise Exception(msg)

        assert 'hazard_layer' in data.keys()
        assert 'exposure_layer' in data.keys()
        assert 'run_duration' in data.keys()
        assert 'run_date' in data.keys()
        assert 'layer' in data.keys()
        assert 'bbox' in data.keys()
        assert 'impact_function' in data.keys()

        layer_uri = data['layer']

        #FIXME: This is not a good way to access the layer name
        typename = layer_uri.split('/')[4]
        name = typename.split(':')[1]
        # Check the autogenerated styles were correctly uploaded
        layer = Layer.objects.get(name=name)

        msg = ('A new style should have been created for layer [%s] '
               'got [%s] style instead.' % (name, layer.default_style.name))
        assert layer.default_style.name == name, msg

    def test_calculate_school_damage(self):
        """Earthquake school damage calculation works via the HTTP REST API
        """

        # Upload required data first
        for filename in ['lembang_mmi_hazmap.asc',
                         'lembang_schools.shp']:
            thefile = os.path.join(TESTDATA, filename)
            uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)
            check_layer(uploaded, full=True)

        # Run calculation through API
        c = Client()
        rv = c.post('/impact/api/calculate/', data=dict(
                   hazard_server=INTERNAL_SERVER_URL,
                   hazard='geonode:lembang_mmi_hazmap',
                   exposure_server=INTERNAL_SERVER_URL,
                   exposure='geonode:lembang_schools',
                   bbox='105.592,-7.809,110.159,-5.647',
                   impact_function='Earthquake Building Damage Function',
                   keywords='test,schools,lembang',
        ))

        msg = 'Expected status code 200, got %i' % rv.status_code
        self.assertEqual(rv.status_code, 200), msg

        msg = ('Expected Content-Type "application/json", '
               'got %s' % rv['Content-Type'])
        self.assertEqual(rv['Content-Type'], 'application/json'), msg

        data = json.loads(rv.content)

        if data['stacktrace'] is not None:
            msg = data['stacktrace']
            raise Exception(msg)

        assert 'hazard_layer' in data.keys()
        assert 'exposure_layer' in data.keys()
        assert 'run_duration' in data.keys()
        assert 'run_date' in data.keys()
        assert 'layer' in data.keys()

        # FIXME (Ole): Download result and check.


if __name__ == '__main__':
    suite = unittest.makeSuite(Test_HTTP, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
