import numpy
import os
import sys
import unittest
import warnings

from django.test.client import Client
from django.conf import settings
from django.utils import simplejson as json

from geonode.maps.utils import get_valid_user
from risiko.utilities import save_to_geonode

from impact.views import calculate
from impact.storage.io import download
from impact.storage.io import get_bounding_box
from impact.storage.io import get_bounding_box_string
from impact.storage.io import read_layer
from impact.storage.io import get_metadata
from impact.tests.utilities import assert_bounding_box_matches, check_layer
from impact.tests.utilities import TESTDATA, DEMODATA, INTERNAL_SERVER_URL


def lembang_damage_function(x):
    if x < 6.0:
        value = 0.0
    else:
        value = (0.692 * (x ** 4) -
                 15.82 * (x ** 3) +
                 135.0 * (x ** 2) -
                 509.0 * x +
                 714.4)
    return value


class Test_calculations(unittest.TestCase):
    """Tests of Risiko calculations
    """

    def setUp(self):
        """Create valid superuser
        """
        self.user = get_valid_user()




    def test_padang_building_examples(self):
        """Padang building impact calculation works through the API
        """

        # Test for a range of hazard layers

        for mmi_filename in ['Shakemap_Padang_2009.asc']:
                             #'Lembang_Earthquake_Scenario.asc']:

            # Upload input data
            hazardfile = os.path.join(DEMODATA, 'hazard', mmi_filename)
            hazard_layer = save_to_geonode(hazardfile, user=self.user)
            hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

            exposurefile = os.path.join(TESTDATA, 'Padang_WSG84.shp')
            exposure_layer = save_to_geonode(exposurefile, user=self.user)
            exposure_name = '%s:%s' % (exposure_layer.workspace,
                                       exposure_layer.name)

            # Call calculation routine

            # FIXME (Ole): The system freaks out if there are spaces in
            #              bbox string. Please let us catch that and deal
            #              nicely with it - also do this in download()
            bbox = '96.956, -5.51, 104.63933, 2.289497'

            #print
            print get_bounding_box(hazardfile)
            #print get_bounding_box(exposurefile)

	    #bbox = get_bounding_box(hazardfile)

            with warnings.catch_warnings():
                warnings.simplefilter('ignore')

                c = Client()
                rv = c.post('/api/v1/calculate/', data=dict(
                        hazard_server=INTERNAL_SERVER_URL,
                        hazard=hazard_name,
                        exposure_server=INTERNAL_SERVER_URL,
                        exposure=exposure_name,
                        bbox=bbox,
                        impact_function='Padang Earthquake Building Damage Function',
                        keywords='test,buildings,padang',
                        ))

            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['Content-Type'], 'application/json')
            data = json.loads(rv.content)
            assert 'hazard_layer' in data.keys()
            assert 'exposure_layer' in data.keys()
            assert 'run_duration' in data.keys()
            assert 'run_date' in data.keys()
            assert 'layer' in data.keys()

            # Download result and check
            layer_name = data['layer'].split('/')[-1]

            result_layer = download(INTERNAL_SERVER_URL,
                                    layer_name,
                                    bbox)
            assert os.path.exists(result_layer.filename)

            # Read hazard data for reference
            hazard_raster = read_layer(hazardfile)
            A = hazard_raster.get_data()
            mmi_min, mmi_max = hazard_raster.get_extrema()

            # Read calculated result
            impact_vector = read_layer(result_layer.filename)
            coordinates = impact_vector.get_geometry()
            attributes = impact_vector.get_data()

            # Verify calculated result
            count = 0
            for i in range(len(attributes)):
                lon, lat = coordinates[i][:]
                calculated_mmi = attributes[i]['MMI']

                if calculated_mmi == 0.0:
                    # FIXME (Ole): Some points have MMI==0 here.
                    # Weird but not a show stopper
                    continue

                # Check that interpolated points are within range
                msg = ('Interpolated mmi %f was outside extrema: '
                       '[%f, %f] at location '
                       '[%f, %f]. ' % (calculated_mmi,
                                       mmi_min, mmi_max,
                                       lon, lat))
                assert mmi_min <= calculated_mmi <= mmi_max, msg

                # Check calculated damage
                calculated_dam = attributes[i]['Percent_da']

                ref_dam = lembang_damage_function(calculated_mmi)
                msg = ('Calculated damage was not as expected '
                       'for hazard layer %s' % hazardfile)
                assert numpy.allclose(calculated_dam, ref_dam,
                                      rtol=1.0e-12), msg

                count += 1

            # Make only a few points were 0
            assert count > len(attributes) - 4



if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'
    suite = unittest.makeSuite(Test_calculations, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
