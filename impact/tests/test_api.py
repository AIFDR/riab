import unittest
from django.test.client import Client
from django.utils import simplejson as json

AIFDR_SERVER = 'http://www.aifdr.org:8080/geoserver/ows'

class Test_HTTP(unittest.TestCase):

    def test_functions(self):
        """Test it is possible to retrieve the list of functions from the HTTP Rest API
        """
        c = Client()

        rv = c.get('/api/v1/functions/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        msg = ('The api should return a dictionary with at least one item. '
               'The key of that item should be "functions"')
        assert 'functions' in data, msg
        functions = data['functions']
        msg = ('No functions were found in the functions list, not even the built-in ones')
        assert len(functions) > 0, msg

    def test_layers(self):
        """Test it is possible to retrieve the list of layers from the HTTP Rest API
        """
        c = Client()

        rv = c.get('/api/v1/layers/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
 

    def test_calculate_fatality(self):
        """Test earthquake fatalities calculation via the HTTP Rest API
        """

        c = Client()
        rv = c.post('/api/v1/calculate/', dict(
                   hazard_server=AIFDR_SERVER,
                   hazard='hazard:Earthquake_Ground_Shaking',
                   exposure='exposure:Population_2010',
                   exposure_server=AIFDR_SERVER,
                   bbox='99.36,-2.199,102.237,0.00',
                   impact_function='Earthquake Fatality Function',
                   impact_level=10,
                   keywords='test,earthquake,fatality',
            ))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        assert 'hazard_layer' in data.keys()
        assert 'exposure_layer' in data.keys()
        assert 'run_duration' in data.keys()
        assert 'run_date' in data.keys()
        assert 'layer' in data.keys()
        assert 'bbox' in data.keys()
        assert 'impact_function' in data.keys()

    def test_calculate_school_damage(self):
        """Test earthquake school damage calculation via the HTTP Rest API
        """
        c = Client()

        rv = c.post('/api/v1/calculate/', data=dict(
                   hazard_server=AIFDR_SERVER,
                   hazard='hazard:lembang_mmi_hazmap',
                   exposure_server=AIFDR_SERVER,
                   exposure='exposure:lembang_schools',
                   bbox='105.592,-7.809,110.159,-5.647',
                   impact_function='Earthquake School Damage Function',
                   impact_level=10,
                   keywords="test,schools,lembang",
        ))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        assert 'hazard_layer' in data.keys()
        assert 'exposure_layer' in data.keys()
        assert 'run_duration' in data.keys()
        assert 'run_date' in data.keys()
        assert 'layer' in data.keys()


if __name__ == '__main__':
   suite = unittest.makeSuite(Test_HTTP, 'test')
   runner = unittest.TextTestRunner(verbosity=2)
   runner.run(suite)
