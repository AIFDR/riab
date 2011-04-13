from geonode.maps.utils import upload, file_upload, GeoNodeException
from impact import storage
from impact.storage import download
from impact.storage.io import get_bounding_box, read_layer
from django.test.client import Client
from django.conf import settings
from django.utils import simplejson as json
from impact.views import calculate

import numpy
import os
import sys
import unittest

internal_server = os.path.join(settings.GEOSERVER_BASE_URL, 'ows')

TEST_DATA = os.path.join(os.environ['RIAB_HOME'],
                         'riab_data', 'risiko_test_data')


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

    def test_io(self):
        """Data can be uploaded and downloaded from internal GeoServer
        """

        # Upload a data set
        for filename in ['lembang_mmi_hazmap.tif', 'lembang_schools.shp']:
            basename, ext = os.path.splitext(filename)

            filename = os.path.join(TEST_DATA, filename)
            layer = file_upload(filename)

            # Name checking
            layer_name = layer.name
            workspace = layer.workspace

            msg = 'Expected workspace to be "geonode". Got %s' % workspace
            assert workspace == 'geonode'

            msg = 'Expected layer name to be "geonode". Got %s' % workspace
            assert workspace == 'geonode', msg

            # Check metadata
            assert isinstance(layer.geographic_bounding_box, basestring)

            # Exctract bounding bounding box from layer handle
            s = 'POLYGON(('
            i = layer.geographic_bounding_box.find(s) + len(s)
            assert i > len(s)

            j = layer.geographic_bounding_box.find('))')
            assert j > i

            bbox_string = str(layer.geographic_bounding_box[i:j])
            A = numpy.array([[float(x[0]), float(x[1])] for x in
                                 (p.split() for p in bbox_string.split(','))])
            south = min(A[:, 1])
            north = max(A[:, 1])
            west = min(A[:, 0])
            east = max(A[:, 0])
            bbox = [west, south, east, north]

            # Check correctness of bounding box against reference
            ref_bbox = get_bounding_box(filename)

            msg = ('Bounding box from layer handle "%s" was not as expected.\n'
                   'Got %s, expected %s' % (layer_name, bbox, ref_bbox))
            assert numpy.allclose(bbox, ref_bbox), msg

            # Download layer again using workspace:name
            downloaded_layer = download(internal_server,
                                        '%s:%s' % (workspace,
                                                   layer_name),
                                        bbox)
            assert os.path.exists(downloaded_layer.filename)

            # Using only name without using workspace
            # FIXME (Ole): This works for raster but not for vector layers
            #
            #downloaded_layer = download(internal_server,
            #                            layer_name,
            #                            bbox)
            #assert os.path.exists(downloaded_layer.filename)

            # Check handling of invalid workspace name
            #try:
            #    downloaded_layer = download(internal_server,
            #                                'glokurp:%s' % layer_name,
            #                                bbox)
            #except:
            #    msg = 'Write exception handling of invalid workspace name'
            #    print msg
            #    #raise Exception(msg)

    def test_lembang_school_example(self):
        """Lembang building impact calculation works through the API
        """

        # Upload input data
        hazardfile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        hazard_layer = file_upload(hazardfile)
        hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

        exposurefile = os.path.join(TEST_DATA, 'lembang_schools.shp')
        exposure_layer = file_upload(exposurefile)
        exposure_name = '%s:%s' % (exposure_layer.workspace,
                                   exposure_layer.name)

        # Call calculation routine
        bbox = '105.592,-7.809,110.159,-5.647'

        #print
        #print get_bounding_box(hazardfile)
        #print get_bounding_box(exposurefile)

        c = Client()
        rv = c.post('/api/v1/calculate/', data=dict(
                hazard_server=internal_server,
                hazard=hazard_name,
                exposure_server=internal_server,
                exposure=exposure_name,
                bbox=bbox,
                impact_function='Earthquake School Damage Function',
                impact_level=10,
                keywords='test,schools,lembang',
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

        result_layer = download(internal_server,
                                layer_name,
                                bbox)
        assert os.path.exists(result_layer.filename)

        # Read hazard data for reference
        hazard_raster = read_layer(hazardfile)
        A = hazard_raster.get_data()
        mmi_min, mmi_max = hazard_raster.get_extrema()

        # Read calculated result
        impact_vector = read_layer(result_layer.filename)
        coordinates, attributes = impact_vector.get_data()

        # Verify calculated result
        count = 0
        for i in range(len(attributes)):
            calculated_mmi = attributes[i]['MMI']

            if calculated_mmi == 0.0:
                # FIXME (Ole): Some points have MMI==0 here.
                # Weird but not a show stopper
                continue

            # Check that interpolated points are within range
            msg = ('Interpolated mmi %f was outside extrema: '
                   '[%f, %f]. ' % (calculated_mmi, mmi_min, mmi_max))
            assert mmi_min <= calculated_mmi <= mmi_max, msg

            # Check calculated damage
            calculated_dam = attributes[i]['Percent_da']

            ref_dam = lembang_damage_function(calculated_mmi)
            msg = ('Calculated damage was not as expected')
            assert numpy.allclose(calculated_dam, ref_dam, rtol=1.0e-12), msg

            count += 1

        # Make only a few points were 0
        assert count > len(attributes) - 4

if __name__ == '__main__':
    import logging

    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'

    # Set up logging
    for _module in ['geonode.maps.utils']:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler())
        # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        _logger.setLevel(logging.CRITICAL)

    suite = unittest.makeSuite(Test_calculations, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
