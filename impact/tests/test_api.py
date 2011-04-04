from riab_server.webapi.views import AIFDR_SERVER
import unittest
from mock import Mock
from riab_server.webapi import storage
from django.test.client import Client
from django.utils import simplejson as json

storage.upload = Mock()
storage.upload.return_value = 'http://dummygeonode.com/data/layer'


class Test_HTTP(unittest.TestCase):

    def test_calculate_fatality(self):
        """Test earthquake fatalities calculation via the HTTP Rest API
        """

        c = Client()
        rv = c.post('/riab/api/v1/calculate/', dict(
                   hazard_server=AIFDR_SERVER,
                   hazard='hazard:Earthquake_Ground_Shaking',
                   exposure='exposure:Population_2010',
                   exposure_server=AIFDR_SERVER,
                   bbox='99.36,-2.199,102.237,0.00',
                   impact_function='EarthquakeFatalityFunction',
                   impact_level=10,
                   keywords='test,earthquake,fatality',
            ))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        assert 'hazard' in data.keys()
        assert 'exposure' in data.keys()
        assert 'run_duration' in data.keys()
        assert 'run_date' in data.keys()
        assert 'result' in data.keys()
        assert 'keywords' in data.keys()
        assert 'bbox' in data.keys()
        assert 'impact_function' in data.keys()

    def test_calculate_school_damage(self):
        """Test earthquake school damage calculation via the HTTP Rest API
        """
        c = Client()

        rv = c.post('/riab/api/v1/calculate/', data=dict(
                   hazard_server=AIFDR_SERVER,
                   hazard='hazard:lembang_mmi_hazmap',
                   exposure_server=AIFDR_SERVER,
                   exposure='exposure:lembang_schools',
                   bbox='105.592,-7.809,110.159,-5.647',
                   impact_function='EarthquakeSchoolDamageFunction',
                   impact_level=10,
                   keywords="test,schools,lembang",
        ))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        assert 'hazard' in data.keys()
        assert 'exposure' in data.keys()
        assert 'run_duration' in data.keys()
        assert 'run_date' in data.keys()
        assert 'result' in data.keys()
        assert 'keywords' in data.keys()


if __name__ == '__main__':
    suite = unittest.makeSuite(Test_HTTP, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
