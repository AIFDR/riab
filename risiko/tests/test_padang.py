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
from risiko.utilities import assert_bounding_box_matches, check_layer

from impact.views import calculate
from impact.storage.io import download
from impact.storage.io import get_bounding_box
from impact.storage.io import get_bounding_box_string
from impact.storage.io import read_layer
from impact.storage.io import get_metadata
from impact.tests.utilities import TESTDATA, DEMODATA, INTERNAL_SERVER_URL


def pandang_check_results(mmi, building_class):
    """Check calculated results through a lookup table
    returns False if the lookup fails and
    an exception if more than one lookup returned"""

    # Reference table established from plugin as of 28 July 2011
    # It was then manually verified against an Excel table by Abbie Baca
    # and Ted Dunstone. Format is
    # MMI, Building class, impact [%]
    padang_verified_results = [
          [7.511692, 1, 50.56493],
          [7.480775, 1, 49.06926],
          [7.638388, 2, 20.30747],
          [7.098015, 2, 5.886142],
          [7.494795, 3, 7.221645],
          [7.610998, 3, 9.348216],
          [7.662717, 4, 3.308273],
          [7.260199, 4, 0.176997],
          [7.144405, 5, 1.075663],
          [7.857333, 5, 7.576518],
          [7.550323, 6, 4.743625],
          [7.470334, 6, 4.082062],
          [7.306306, 6, 2.942894],
          [7.528476, 7, 1.281912],
          [7.098805, 7, 0.150739],
          [7.603434, 8, 1.224659],
          [7.442411, 8, 0.530800],
          [7.400580, 8, 0.419928],
          [7.397977, 8, 0.413749],
          [7.450592, 8, 0.555220],
          [7.453757, 8, 0.564922],
          [7.445377, 8, 0.539542],
          [7.433962, 8, 0.506559],
          [7.424470, 8, 0.480477],
          [7.439781, 8, 0.523150],
          [7.398985, 8, 0.416132],
          [7.435351, 8, 0.510478],
          [7.446795, 8, 0.543766],
          [7.454428, 8, 0.567000],
          [7.401520, 8, 0.422178],
          [7.397964, 8, 0.413719],
          [7.396476, 8, 0.410224],
          [7.638214, 9, 1.694369],
          [7.427594, 9, 1.050452],
          [7.345935, 9, 0.862066]]

    impact_array = [verified_impact
        for verified_mmi, verified_building_class, verified_impact
               in padang_verified_results
                    if numpy.allclose(verified_mmi, mmi, rtol=1.0e-6) and
                    numpy.allclose(verified_building_class, building_class,
                                   rtol=1.0e-6)]

    if len(impact_array) == 0:
        return False
    elif len(impact_array) == 1:
        return impact_array[0]

    assert len(impact_array) < 2, 'More than one lookup " \
                    "result returned. May be precision error.'


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
            hazard_name = '%s:%s' % (hazard_layer.workspace,
                                        hazard_layer.name)

            exposurefile = os.path.join(TESTDATA, 'Padang_WGS84.shp')
            exposure_layer = save_to_geonode(exposurefile, user=self.user)
            exposure_name = '%s:%s' % (exposure_layer.workspace,
                                          exposure_layer.name)

            # Call calculation routine

            # FIXME (Ole): The system freaks out if there are spaces in
            #              bbox string. Please let us catch that and deal
            #              nicely with it - also do this in download()
            bbox = '96.956, -5.51, 104.63933, 2.289497'

            with warnings.catch_warnings():
                warnings.simplefilter('ignore')

                c = Client()
                rv = c.post('/api/v1/calculate/', data=dict(
                            hazard_server=INTERNAL_SERVER_URL,
                            hazard=hazard_name,
                            exposure_server=INTERNAL_SERVER_URL,
                            exposure=exposure_name,
                            bbox=bbox,
                            impact_function='Padang Earthquake ' \
                                            'Building Damage Function',
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
                verified_count = 0
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

                    building_class = attributes[i]['TestBLDGCl']

                    # Check calculated damage
                    calculated_dam = attributes[i]['DAMAGE']
                    verified_dam = pandang_check_results(calculated_mmi,
                                                         building_class)
                    if verified_dam != False:

                        msg = ('Calculated damage was not as expected '
                                 'for hazard layer %s. I got %f '
                               'but expected %f' % (hazardfile,
                                                    calculated_dam,
                                                    verified_dam))
                        assert numpy.allclose(calculated_dam, verified_dam,
                                               rtol=1.0e-4), msg
                        verified_count += 1
                    count += 1

                msg = ('No points was verified in output. Please create '
                       'table withe reference data')
                assert verified_count > 0, msg
                assert count == 3802, 'Number buildings was not 3802.'


if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'
    suite = unittest.makeSuite(Test_calculations, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
