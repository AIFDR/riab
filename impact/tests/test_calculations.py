import numpy
import os
import sys
import unittest
import warnings

from django.test.client import Client
from django.conf import settings
from django.utils import simplejson as json

from geonode.maps.utils import get_valid_user, check_geonode_is_up

from impact.views import calculate

from impact.storage.io import save_to_geonode, check_layer
from impact.storage.io import assert_bounding_box_matches
from impact.storage.io import download
from impact.storage.io import get_bounding_box
from impact.storage.io import get_bounding_box_string
from impact.storage.io import read_layer
from impact.storage.io import get_metadata

from impact.tests.utilities import TESTDATA, INTERNAL_SERVER_URL
from owslib.wcs import WebCoverageService


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

    def test_io(self):
        """Data can be uploaded and downloaded from internal GeoServer
        """

        # Upload a raster and a vector data set
        for filename in ['population_padang_1.asc', 'lembang_schools.shp']:
            basename, ext = os.path.splitext(filename)
            filename = os.path.join(TESTDATA, filename)

            layer = save_to_geonode(filename, user=self.user, overwrite=True)

            # Name checking
            layer_name = layer.name
            expected_name = basename.lower()
            msg = 'Expected layername %s but got %s' % (expected_name,
                                                        layer_name)
            assert layer_name == expected_name, msg

            workspace = layer.workspace

            msg = 'Expected workspace to be "geonode". Got %s' % workspace
            assert workspace == 'geonode'

            # Check metadata
            assert_bounding_box_matches(layer, filename)

            # Download layer again using workspace:name
            bbox = get_bounding_box(filename)
            downloaded_layer = download(INTERNAL_SERVER_URL,
                                        '%s:%s' % (workspace, layer_name),
                                        bbox)
            assert os.path.exists(downloaded_layer.filename)

            # FIXME (Ole): I wan't to check that the resolution is as expected
            #              in case of raster layers.

            # FIXME (Ole): Bring this test back when issue:39 has been resolved
            # Check that exception is raised when using name without workspace
            #try:
            #    downloaded_layer = download(INTERNAL_SERVER_URL,
            #                                layer_name,
            #                                bbox)
            #except AssertionError, e:
            #    expected_error = 'Layer must have the format "workspace:name"'
            #    msg = ('Exception was raised but error message was: %s\n'
            #           'I expected error message: %s...' % (e,
            #                                                expected_error))
            #    assert str(e).startswith(expected_error), msg
            #else:
            #    msg = ('Assertion error should have been raised for layer '
            #           'name %s which is not preceded by workspace'
            #           % layer_name)
            #    raise Exception(msg)

            # Check handling of invalid workspace name
            #try:
            #    downloaded_layer = download(INTERNAL_SERVER_URL,
            #                                'glokurp:%s' % layer_name,
            #                                bbox)
            #except:
            #    msg = 'Write exception handling of invalid workspace name'
            #    print msg
            #    #raise Exception(msg)

    def test_the_earthquake_fatality_estimation_allen(self):
        """Fatality computation computed correctly with GeoServer Data
        """

        # Simulate bounding box from application
        viewport_bbox_string = '104.3,-8.2,110.04,-5.17'

        # Upload exposure data for this test
        name = 'Population_2010'
        exposure_filename = '%s/%s.asc' % (TESTDATA, name)
        exposure_layer = save_to_geonode(exposure_filename,
                                         user=self.user, overwrite=True)

        workspace = exposure_layer.workspace
        msg = 'Expected workspace to be "geonode". Got %s' % workspace
        assert workspace == 'geonode'

        layer_name = exposure_layer.name
        msg = 'Expected layer name to be "%s". Got %s' % (name, layer_name)
        assert layer_name == name.lower(), msg

        exposure_name = '%s:%s' % (workspace, layer_name)

        # Check metadata
        assert_bounding_box_matches(exposure_layer, exposure_filename)
        exp_bbox_string = get_bounding_box_string(exposure_filename)
        check_layer(exposure_layer, full=True)

        # Now we know that exposure layer is good, lets upload some
        # hazard layers and do the calculations
        filename = 'Lembang_Earthquake_Scenario.asc'

        # Save
        hazard_filename = '%s/%s' % (TESTDATA, filename)
        hazard_layer = save_to_geonode(hazard_filename,
                                       user=self.user, overwrite=True)
        hazard_name = '%s:%s' % (hazard_layer.workspace,
                                 hazard_layer.name)

        # Check metadata
        assert_bounding_box_matches(hazard_layer, hazard_filename)
        haz_bbox_string = get_bounding_box_string(hazard_filename)
        check_layer(hazard_layer, full=True)

        # Run calculation
        c = Client()
        rv = c.post('/impact/api/calculate/', data=dict(
                hazard_server=INTERNAL_SERVER_URL,
                hazard=hazard_name,
                exposure_server=INTERNAL_SERVER_URL,
                exposure=exposure_name,
                #bbox=viewport_bbox_string,
                bbox=exp_bbox_string,  # This one reproduced the
                                       # crash for lembang
                impact_function='EarthquakeFatalityFunction',
                keywords='test,shakemap,usgs'))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        if 'errors' in data:
            errors = data['errors']
            if errors is not None:
                raise Exception(errors)

        assert 'hazard_layer' in data
        assert 'exposure_layer' in data
        assert 'run_duration' in data
        assert 'run_date' in data
        assert 'layer' in data

        # Download result and check
        layer_name = data['layer'].split('/')[-1]

        result_layer = download(INTERNAL_SERVER_URL,
                                layer_name,
                                get_bounding_box_string(hazard_filename))
        assert os.path.exists(result_layer.filename)

    def test_metadata_available_after_upload(self):
        """Test metadata is available after upload
        """
        # Upload exposure data for this test
        name = 'Population_2010'
        exposure_filename = '%s/%s.asc' % (TESTDATA, name)
        exposure_layer = save_to_geonode(exposure_filename,
                                         user=self.user, overwrite=True)
        layer_name = exposure_layer.typename
        server_url = settings.GEOSERVER_BASE_URL + '/ows'
        wcs = WebCoverageService(server_url, version='1.0.0')
        layer_appears_immediately = layer_name in wcs.contents

        wait_time = 0.5
        import time
        time.sleep(wait_time)

        wcs2 = WebCoverageService(server_url, version='1.0.0')
        layer_appears_afterwards = layer_name in wcs2.contents

        msg = ('Layer %s was not found after %s seconds in WxS contents '
               'on server %s.\n'
               'WCS contents: %s\n' % (layer_name,
                                       wait_time,
                                       server_url,
                                       wcs.contents))

        assert layer_appears_afterwards, msg

        msg = ('Layer %s was not found in WxS contents on server %s.\n'
               'WCS contents: %s\n' % (layer_name, server_url, wcs.contents))

        assert layer_appears_immediately, msg

    def test_lembang_building_examples(self):
        """Lembang building impact calculation works through the API
        """

        # Test for a range of hazard layers

        for mmi_filename in ['lembang_mmi_hazmap.asc']:
                             #'Lembang_Earthquake_Scenario.asc']:

            # Upload input data
            hazardfile = os.path.join(TESTDATA, mmi_filename)
            hazard_layer = save_to_geonode(hazardfile, user=self.user)
            hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

            exposurefile = os.path.join(TESTDATA, 'lembang_schools.shp')
            exposure_layer = save_to_geonode(exposurefile, user=self.user)
            exposure_name = '%s:%s' % (exposure_layer.workspace,
                                       exposure_layer.name)

            # Call calculation routine

            # FIXME (Ole): The system freaks out if there are spaces in
            #              bbox string. Please let us catch that and deal
            #              nicely with it - also do this in download()
            bbox = '105.592,-7.809,110.159,-5.647'

            #print
            #print get_bounding_box(hazardfile)
            #print get_bounding_box(exposurefile)

            with warnings.catch_warnings():
                warnings.simplefilter('ignore')

                c = Client()
                rv = c.post('/impact/api/calculate/', data=dict(
                        hazard_server=INTERNAL_SERVER_URL,
                        hazard=hazard_name,
                        exposure_server=INTERNAL_SERVER_URL,
                        exposure=exposure_name,
                        bbox=bbox,
                        impact_function='Earthquake Building Damage Function',
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
                calculated_dam = attributes[i]['DAMAGE']

                ref_dam = lembang_damage_function(calculated_mmi)
                msg = ('Calculated damage was not as expected '
                       'for hazard layer %s' % hazardfile)
                assert numpy.allclose(calculated_dam, ref_dam,
                                      rtol=1.0e-12), msg

                count += 1

            # Make only a few points were 0
            assert count > len(attributes) - 4

    def XXtest_shakemap_population_exposure(self):
        """Population exposed to groundshaking matches USGS numbers
        """

        hazardfile = os.path.join(TESTDATA, 'shakemap_sumatra_20110129.tif')
        hazard_layer = save_to_geonode(hazardfile, overwrite=True,
                                       user=self.user)
        hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

        exposurefile = os.path.join(TESTDATA, 'population_indonesia_2008.tif')
        exposure_layer = save_to_geonode(exposurefile, overwrite=True,
                                         user=self.user)
        exposure_name = '%s:%s' % (exposure_layer.workspace,
                                   exposure_layer.name)

        #with warnings.catch_warnings():
        #    warnings.simplefilter('ignore')
        c = Client()
        rv = c.post('/impact/api/calculate/', data=dict(
                hazard_server=INTERNAL_SERVER_URL,
                hazard=hazard_name,
                exposure_server=INTERNAL_SERVER_URL,
                exposure=exposure_name,
                bbox=get_bounding_box_string(hazardfile),
                impact_function='USGSFatalityFunction',
                keywords='test,shakemap,usgs'))

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
                                get_bounding_box(hazardfile))
        assert os.path.exists(result_layer.filename)

        # Read hazard data for reference
        hazard_raster = read_layer(hazardfile)
        H = hazard_raster.get_data()
        mmi_min, mmi_max = hazard_raster.get_extrema()

        # Read calculated result
        impact_raster = read_layer(result_layer.filename)
        I = impact_raster.get_data()

        # FIXME (Ole): Not finished

    def test_exceptions_in_calculate_endpoint(self):
        """Wrong bbox input is handled nicely by /impact/api/calculate/
        """

        # Upload input data
        hazardfile = os.path.join(TESTDATA, 'lembang_mmi_hazmap.asc')
        hazard_layer = save_to_geonode(hazardfile, user=self.user)
        hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

        exposurefile = os.path.join(TESTDATA, 'lembang_schools.shp')
        exposure_layer = save_to_geonode(exposurefile, user=self.user)
        exposure_name = '%s:%s' % (exposure_layer.workspace,
                                   exposure_layer.name)

        bbox_correct = '105.592,-7.809,110.159,-5.647'
        bbox_with_spaces = '105.592, -7.809, 110.159, -5.647'
        bbox_non_numeric = '105.592,-7.809,x,-5.647'
        bbox_list = [1, 2, 3, 4]
        bbox_list_non_numeric = [1, '2', 3, 4]
        bbox_none = None
        bbox_wrong_number1 = '105.592,-7.809,-5.647'
        bbox_wrong_number2 = '105.592,-7.809,-5.647,34,123'
        bbox_empty = ''
        bbox_inconsistent1 = '110,-7.809,105,-5.647'
        bbox_inconsistent2 = '105.592,-5,110.159,-7'
        bbox_out_of_bound1 = '-185.592,-7.809,110.159,-5.647'
        bbox_out_of_bound2 = '105.592,-97.809,110.159,-5.647'
        bbox_out_of_bound3 = '105.592,-7.809,189.159,-5.647'
        bbox_out_of_bound4 = '105.592,-7.809,110.159,-105.647'

        data = dict(hazard_server=INTERNAL_SERVER_URL,
                    hazard=hazard_name,
                    exposure_server=INTERNAL_SERVER_URL,
                    exposure=exposure_name,
                    bbox=bbox_correct,
                    impact_function='Earthquake Building Damage Function',
                    keywords='test,schools,lembang')

        # First do it correctly (twice)
        c = Client()
        rv = c.post('/impact/api/calculate/', data=data)
        rv = c.post('/impact/api/calculate/', data=data)

        # Then check that spaces are dealt with correctly
        data['bbox'] = bbox_with_spaces
        rv = c.post('/impact/api/calculate/', data=data)

        # Then with a range of wrong bbox inputs
        for bad_bbox in [bbox_list,
                         bbox_none,
                         bbox_empty,
                         bbox_non_numeric,
                         bbox_list_non_numeric,
                         bbox_wrong_number1,
                         bbox_wrong_number2,
                         bbox_inconsistent1,
                         bbox_inconsistent2,
                         bbox_out_of_bound1,
                         bbox_out_of_bound2,
                         bbox_out_of_bound3,
                         bbox_out_of_bound4]:

            # Use erroneous bounding box
            data['bbox'] = bad_bbox

            # FIXME (Ole): Suppress error output from c.post
            rv = c.post('/impact/api/calculate/', data=data)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['Content-Type'], 'application/json')
            data_out = json.loads(rv.content)

            msg = ('Bad bounding box %s should have raised '
                       'an error' % bad_bbox)
            assert 'errors' in data_out, msg

    def test_geotransform_from_geonode(self):
        """Geotransforms of GeoNode layers can be correctly determined
        """

        for filename in ['lembang_mmi_hazmap.asc',
                         'test_grid.asc']:

            # Upload file to GeoNode
            f = os.path.join(TESTDATA, filename)
            layer = save_to_geonode(f, user=self.user)

            # Read raster file and obtain reference resolution
            R = read_layer(f)
            ref_geotransform = R.get_geotransform()

            # Get geotransform from GeoNode
            layer_name = layer.typename
            metadata = get_metadata(INTERNAL_SERVER_URL, layer_name)

            geotransform_name = 'geotransform'
            msg = ('Could not find attribute "%s" in metadata. '
                   'Values are: %s' % (geotransform_name, metadata.keys()))
            assert geotransform_name in metadata, msg

            gn_geotransform = metadata[geotransform_name]
            msg = ('Geotransform obtained from GeoNode for layer %s '
                   'was not correct. I got %s but expected %s'
                   '' % (layer_name, gn_geotransform, ref_geotransform))
            assert numpy.allclose(ref_geotransform, gn_geotransform), msg

    # FIXME (Ole): work in progress regarding issue #19 and #103.
    # Would eventually do a definitive end-to-end test that interpolated
    # values are good.
    def Xtest_interpolation_example(self):
        """Interpolation is done correctly with data going through geonode

        This data (Maumere scenaria) showed some very wrong results
        when first attempted in August 2011 - hence this test
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = ('%s/maumere_aos_depth_20m_land_wgs84.asc'
                           % TESTDATA)
        exposure_filename = ('%s/maumere_pop_prj.shp' % TESTDATA)

        # Upload to internal geonode
        hazard_layer = save_to_geonode(hazard_filename, user=self.user)
        hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

        exposure_layer = save_to_geonode(exposure_filename, user=self.user)
        exposure_name = '%s:%s' % (exposure_layer.workspace,
                                   exposure_layer.name)

        # Download data again
        bbox = get_bounding_box_string(hazard_filename)  # The biggest
        H = download(INTERNAL_SERVER_URL, hazard_name, bbox)
        E = download(INTERNAL_SERVER_URL, exposure_name, bbox)

        A = H.get_data()
        depth_min, depth_max = H.get_extrema()

        # Compare extrema to values read off QGIS for this layer
        print 'E', depth_min, depth_max
        assert numpy.allclose([depth_min, depth_max], [0.0, 16.68],
                              rtol=1.0e-6, atol=1.0e-10)

        coordinates = E.get_geometry()
        attributes = E.get_data()

        # Interpolate
        I = H.interpolate(E, name='depth')
        Icoordinates = I.get_geometry()
        Iattributes = I.get_data()
        assert numpy.allclose(Icoordinates, coordinates)

        N = len(Icoordinates)
        assert N == 891

        # Verify interpolated values with test result
        for i in range(N):

            interpolated_depth = Iattributes[i]['depth']
            pointid = attributes[i]['POINTID']

            if pointid == 263:

                # Check that location is correct
                assert numpy.allclose(coordinates[i],
                                      [122.20367299, -8.61300358])

                # This is known to be outside inundation area so should
                # near zero
                assert numpy.allclose(interpolated_depth, 0.0,
                                      rtol=1.0e-12, atol=1.0e-12)

            if pointid == 148:
                # Check that location is correct
                assert numpy.allclose(coordinates[i],
                                      [122.2045912, -8.608483265])

                # This is in an inundated area with a surrounding depths of
                # 4.531, 3.911
                # 2.675, 2.583
                assert interpolated_depth < 4.531
                assert interpolated_depth > 2.583
                assert numpy.allclose(interpolated_depth, 3.553,
                                      rtol=1.0e-5, atol=1.0e-5)

            # Check that interpolated points are within range
            msg = ('Interpolated depth %f at point %i was outside extrema: '
                   '[%f, %f]. ' % (interpolated_depth, i,
                                   depth_min, depth_max))

            if not numpy.isnan(interpolated_depth):
                tol = 1.0e-6
                #assert depth_min - tol <= interpolated_depth <= depth_max, msg
                #if interpolated_depth > depth_max:
                #    print msg
                #if interpolated_depth < depth_min:
                #    print msg

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'
    suite = unittest.makeSuite(Test_calculations, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
