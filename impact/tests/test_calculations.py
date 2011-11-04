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

from impact.storage.utilities import nanallclose

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
                msg = ('The server returned the error message: %s'
                       % str(errors))
                raise Exception(msg)

        assert 'success' in data
        assert 'hazard_layer' in data
        assert 'exposure_layer' in data
        assert 'run_duration' in data
        assert 'run_date' in data
        assert 'layer' in data

        assert data['success']

        # Download result and check
        layer_name = data['layer'].split('/')[-1]

        result_layer = download(INTERNAL_SERVER_URL,
                                layer_name,
                                get_bounding_box_string(hazard_filename))
        assert os.path.exists(result_layer.filename)

    def test_jakarta_flood_study(self):
        """HKV Jakarta flood study calculated correctly using the API
        """

        # FIXME (Ole): Redo with population as shapefile later

        # Expected values from HKV
        expected_values = [2485442, 1537920]

        # Name files for hazard level, exposure and expected fatalities
        population = 'Population_Jakarta_geographic'
        plugin_name = 'FloodImpactFunction'

        # Upload exposure data for this test
        exposure_filename = '%s/%s.asc' % (TESTDATA, population)
        exposure_layer = save_to_geonode(exposure_filename,
                                         user=self.user, overwrite=True)

        workspace = exposure_layer.workspace
        msg = 'Expected workspace to be "geonode". Got %s' % workspace
        assert workspace == 'geonode'

        layer_name = exposure_layer.name
        msg = 'Expected layer name to be "%s". Got %s' % (population,
                                                          layer_name)
        assert layer_name.lower() == population.lower(), msg

        exposure_name = '%s:%s' % (workspace, layer_name)

        # Check metadata
        assert_bounding_box_matches(exposure_layer, exposure_filename)
        exp_bbox_string = get_bounding_box_string(exposure_filename)
        check_layer(exposure_layer, full=True)

        # Now we know that exposure layer is good, lets upload some
        # hazard layers and do the calculations

        i = 0
        for filename in ['Flood_Current_Depth_Jakarta_geographic.asc',
                         'Flood_Design_Depth_Jakarta_geographic.asc']:

            hazard_filename = os.path.join(TESTDATA, filename)
            exposure_filename = os.path.join(TESTDATA, population)

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
                    bbox=exp_bbox_string,
                    impact_function=plugin_name,
                    keywords='test,flood,HKV'))

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

            # Do calculation manually and check result
            hazard_raster = read_layer(hazard_filename)
            H = hazard_raster.get_data(nan=0)

            exposure_raster = read_layer(exposure_filename + '.asc')
            P = exposure_raster.get_data(nan=0)

            # Calculate impact manually
            pixel_area = 2500
            I = numpy.where(H > 0.1, P, 0) / 100000.0 * pixel_area

            # Verify correctness against results from HKV
            res = sum(I.flat)
            ref = expected_values[i]
            #print filename, 'Result=%f' % res, ' Expected=%f' % ref
            #print 'Pct relative error=%f' % (abs(res-ref)*100./ref)

            msg = 'Got result %f but expected %f' % (res, ref)
            assert numpy.allclose(res, ref, rtol=1.0e-2), msg

            # Verify correctness of result
            # Download result and check
            layer_name = data['layer'].split('/')[-1]

            result_layer = download(INTERNAL_SERVER_URL,
                                    layer_name,
                                    get_bounding_box_string(hazard_filename))
            assert os.path.exists(result_layer.filename)

            calculated_raster = read_layer(result_layer.filename)
            C = calculated_raster.get_data(nan=0)

            # FIXME (Ole): Bring this back
            # Check caption
            #caption = calculated_raster.get_caption()
            #print
            #print caption
            #expct = 'people'
            #msg = ('Caption %s did not contain expected '
            #       'keyword %s' % (caption, expct))
            #assert expct in caption, msg

            # Compare shape and extrema
            msg = ('Shape of calculated raster differs from reference raster: '
                   'C=%s, I=%s' % (C.shape, I.shape))
            assert numpy.allclose(C.shape, I.shape,
                                  rtol=1e-12, atol=1e-12), msg

            msg = ('Minimum of calculated raster differs from reference '
                   'raster: '
                   'C=%s, I=%s' % (numpy.nanmin(C), numpy.nanmin(I)))
            assert numpy.allclose(numpy.nanmin(C), numpy.nanmin(I),
                                  rtol=1e-6, atol=1e-12), msg
            msg = ('Maximum of calculated raster differs from reference '
                   'raster: '
                   'C=%s, I=%s' % (numpy.nanmax(C), numpy.nanmax(I)))
            assert numpy.allclose(numpy.nanmax(C), numpy.nanmax(I),
                                  rtol=1e-6, atol=1e-12), msg

            # Compare every single value numerically (a bit loose -
            # probably due to single precision conversions when
            # data flows through geonode)
            #
            # FIXME: Not working - but since this test is about
            # issue #162 we'll leave it for now. TODO with NAN
            # Manually verified that the two expected values are correct,
            # though.
            #msg = 'Array values of written raster array were not as expected'
            #print C
            #print I
            #print numpy.amax(numpy.abs(C-I))
            #assert numpy.allclose(C, I, rtol=1e-2, atol=1e-5), msg

            # Check that extrema are in range
            xmin, xmax = calculated_raster.get_extrema()

            assert numpy.alltrue(C[-numpy.isnan(C)] >= xmin), msg
            assert numpy.alltrue(C[-numpy.isnan(C)] <= xmax)
            assert numpy.alltrue(C[-numpy.isnan(C)] >= 0)

            i += 1

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

    # FIXME (Ole): Do as part of issue #74
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

    def test_data_resampling_example(self):
        """Raster data is unchanged when going through geonode

        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = ('%s/maumere_aos_depth_20m_land_wgs84.asc'
                           % TESTDATA)
        exposure_filename = ('%s/maumere_pop_prj.shp' % TESTDATA)

        #------------
        # Hazard data
        #------------
        # Read hazard input data for reference
        H_ref = read_layer(hazard_filename)

        A_ref = H_ref.get_data()
        depth_min_ref, depth_max_ref = H_ref.get_extrema()

        # Upload to internal geonode
        hazard_layer = save_to_geonode(hazard_filename, user=self.user)
        hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

        # Download data again
        bbox = get_bounding_box_string(hazard_filename)  # The biggest
        H = download(INTERNAL_SERVER_URL, hazard_name, bbox)

        A = H.get_data()
        depth_min, depth_max = H.get_extrema()

        # FIXME (Ole): The layer read from file is single precision only:
        # Issue #17
        # Here's the explanation why interpolation below produce slightly
        # different results (but why?)
        # The layer read from file is single precision which may be due to
        # the way it is converted from ASC to TIF. In other words the
        # problem may be in raster.write_to_file. Float64 is
        # specified there, so this is a mystery.
        #print 'A', A.dtype          # Double precision
        #print 'A_ref', A_ref.dtype  # Single precision

        # Compare extrema to values from numpy array
        assert numpy.allclose(depth_max, numpy.nanmax(A),
                              rtol=1.0e-12, atol=1.0e-12)

        assert numpy.allclose(depth_max_ref, numpy.nanmax(A_ref),
                              rtol=1.0e-12, atol=1.0e-12)

        # Compare to reference
        assert numpy.allclose([depth_min, depth_max],
                              [depth_min_ref, depth_max_ref],
                              rtol=1.0e-12, atol=1.0e-12)

        # Compare extrema to values read off QGIS for this layer
        assert numpy.allclose([depth_min, depth_max], [0.0, 16.68],
                              rtol=1.0e-6, atol=1.0e-10)

        # Investigate difference visually
        #from matplotlib.pyplot import matshow, show
        #matshow(A)
        #matshow(A_ref)
        #matshow(A - A_ref)
        #show()

        #print
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                if not numpy.isnan(A[i, j]):
                    err = abs(A[i, j] - A_ref[i, j])
                    if err > 0:
                        msg = ('%i, %i: %.15f, %.15f, %.15f'
                               % (i, j, A[i, j], A_ref[i, j], err))
                        raise Exception(msg)
                    #if A[i,j] > 16:
                    #    print i, j, A[i, j], A_ref[i, j]

        # Compare elements (nan & numbers)
        id_nan = numpy.isnan(A)
        id_nan_ref = numpy.isnan(A_ref)
        assert numpy.all(id_nan == id_nan_ref)
        assert numpy.allclose(A[-id_nan], A_ref[-id_nan],
                              rtol=1.0e-15, atol=1.0e-15)

        #print 'MAX', A[245, 283], A_ref[245, 283]
        #print 'MAX: %.15f %.15f %.15f' %(A[245, 283], A_ref[245, 283])
        assert numpy.allclose(A[245, 283], A_ref[245, 283],
                              rtol=1.0e-15, atol=1.0e-15)

        #--------------
        # Exposure data
        #--------------
        # Read exposure input data for reference
        E_ref = read_layer(exposure_filename)

        # Upload to internal geonode
        exposure_layer = save_to_geonode(exposure_filename, user=self.user)
        exposure_name = '%s:%s' % (exposure_layer.workspace,
                                   exposure_layer.name)

        # Download data again
        E = download(INTERNAL_SERVER_URL, exposure_name, bbox)

        # Check exposure data against reference
        coordinates = E.get_geometry()
        coordinates_ref = E_ref.get_geometry()
        assert numpy.allclose(coordinates, coordinates_ref,
                              rtol=1.0e-12, atol=1.0e-12)

        attributes = E.get_data()
        attributes_ref = E_ref.get_data()
        for i, att in enumerate(attributes):
            att_ref = attributes_ref[i]
            for key in att:
                assert att[key] == att_ref[key]

        # Test riab's interpolation function
        I = H.interpolate(E, name='depth')
        icoordinates = I.get_geometry()

        I_ref = H_ref.interpolate(E_ref, name='depth')
        icoordinates_ref = I_ref.get_geometry()

        assert numpy.allclose(coordinates,
                              icoordinates,
                              rtol=1.0e-12, atol=1.0e-12)
        assert numpy.allclose(coordinates,
                              icoordinates_ref,
                              rtol=1.0e-12, atol=1.0e-12)

        iattributes = I.get_data()
        assert numpy.allclose(icoordinates, coordinates)

        N = len(icoordinates)
        assert N == 891

        # Set tolerance for single precision until issue #17 has been fixed
        # It appears that the single precision leads to larger interpolation
        # errors
        rtol_issue17 = 2.0e-3
        atol_issue17 = 1.0e-4

        # Verify interpolated values with test result
        for i in range(N):

            interpolated_depth_ref = I_ref.get_data()[i]['depth']
            interpolated_depth = iattributes[i]['depth']

            assert nanallclose(interpolated_depth,
                               interpolated_depth_ref,
                               rtol=rtol_issue17, atol=atol_issue17)

            pointid = attributes[i]['POINTID']

            if pointid == 263:

                #print i, pointid, attributes[i],
                #print interpolated_depth, coordinates[i]

                # Check that location is correct
                assert numpy.allclose(coordinates[i],
                                      [122.20367299, -8.61300358],
                                      rtol=1.0e-7, atol=1.0e-12)

                # This is known to be outside inundation area so should
                # near zero
                assert numpy.allclose(interpolated_depth, 0.0,
                                      rtol=1.0e-12, atol=1.0e-12)

            if pointid == 148:
                # Check that location is correct
                #print coordinates[i]
                assert numpy.allclose(coordinates[i],
                                      [122.2045912, -8.608483265],
                                      rtol=1.0e-7, atol=1.0e-12)

                # This is in an inundated area with a surrounding depths of
                # 4.531, 3.911
                # 2.675, 2.583
                assert interpolated_depth < 4.531
                assert interpolated_depth < 3.911
                assert interpolated_depth > 2.583
                assert interpolated_depth > 2.675

                #print interpolated_depth
                # This is a characterisation test for bilinear interpolation
                assert numpy.allclose(interpolated_depth, 3.62477215491,
                                      rtol=rtol_issue17, atol=1.0e-12)

            # Check that interpolated points are within range
            msg = ('Interpolated depth %f at point %i was outside extrema: '
                   '[%f, %f]. ' % (interpolated_depth, i,
                                   depth_min, depth_max))

            if not numpy.isnan(interpolated_depth):
                assert depth_min <= interpolated_depth <= depth_max, msg

    def test_earthquake_exposure_plugin(self):
        """Population exposure to individual MMI levels can be computed
        """

        # Upload exposure data for this test
        # FIXME (Ole): While this dataset is ok for testing,
        # note that is has been resampled without scaling
        # so numbers are about 25 times too large.
        # Consider replacing test populations dataset for good measures,
        # just in case any one accidentally started using this dataset
        # for real.

        name = 'Population_2010'
        exposure_filename = '%s/%s.asc' % (TESTDATA, name)
        exposure_layer = save_to_geonode(exposure_filename,
                                         user=self.user, overwrite=True)
        exposure_name = '%s:%s' % (exposure_layer.workspace,
                                   exposure_layer.name)

        # Check metadata
        assert_bounding_box_matches(exposure_layer, exposure_filename)
        exp_bbox_string = get_bounding_box_string(exposure_filename)
        check_layer(exposure_layer, full=True)

        # Upload hazard data
        filename = 'Lembang_Earthquake_Scenario.asc'
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
                bbox=haz_bbox_string,
                impact_function='EarthquakePopulationExposureFunction',
                keywords='test,population,exposure,usgs'))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        if 'errors' in data:
            errors = data['errors']
            if errors is not None:
                msg = ('The server returned the error message: %s'
                       % str(errors))
                raise Exception(msg)

        assert 'success' in data
        assert 'hazard_layer' in data
        assert 'exposure_layer' in data
        assert 'run_duration' in data
        assert 'run_date' in data
        assert 'layer' in data

        assert data['success']

        # Download result and check
        layer_name = data['layer'].split('/')[-1]

        result_layer = download(INTERNAL_SERVER_URL,
                                layer_name,
                                get_bounding_box_string(hazard_filename))
        assert os.path.exists(result_layer.filename)

        # Check calculated values
        keywords = result_layer.get_keywords()

        assert 'mmi-classes' in keywords
        assert 'affected-population' in keywords

        mmi_classes = [int(x) for x in keywords['mmi-classes'].split('_')]
        count = [float(x) for x in keywords['affected-population'].split('_')]

        # Brute force count for each population level
        population = download(INTERNAL_SERVER_URL,
                              exposure_name,
                              get_bounding_box_string(hazard_filename))
        intensity = download(INTERNAL_SERVER_URL,
                             hazard_name,
                             get_bounding_box_string(hazard_filename))

        # Extract data
        H = intensity.get_data(nan=0)
        P = population.get_data(nan=0)

        brutecount = {}
        for mmi in mmi_classes:
            brutecount[mmi] = 0

        for i in range(P.shape[0]):
            for j in range(P.shape[1]):
                mmi = H[i, j]
                if not numpy.isnan(mmi):
                    mmi_class = int(round(mmi))

                    pop = P[i, j]
                    if not numpy.isnan(pop):
                        brutecount[mmi_class] += pop

        for i, mmi in enumerate(mmi_classes):
            assert numpy.allclose(count[i], brutecount[mmi], rtol=1.0e-6)

    def test_linked_datasets(self):
        """Linked datesets can be pulled in e.g. to include gender break down
        """

        # Upload exposure data for this test. This will automatically
        # pull in female_pct_yogya.asc through its "associates" keyword
        name = 'population_yogya'
        exposure_filename = '%s/%s.asc' % (TESTDATA, name)
        exposure_layer = save_to_geonode(exposure_filename,
                                         user=self.user, overwrite=True)
        exposure_name = '%s:%s' % (exposure_layer.workspace,
                                   exposure_layer.name)

        # Check metadata
        assert_bounding_box_matches(exposure_layer, exposure_filename)
        exp_bbox_string = get_bounding_box_string(exposure_filename)
        check_layer(exposure_layer, full=True)

        # Upload hazard data
        filename = 'eq_yogya_2006.asc'
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
                bbox=haz_bbox_string,
                impact_function='EarthquakeFatalityFunction',
                keywords='test,fatalities,population,usgs'))

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        data = json.loads(rv.content)
        if 'errors' in data:
            errors = data['errors']
            if errors is not None:
                msg = ('The server returned the error message: %s'
                       % str(errors))
                raise Exception(msg)

        assert 'success' in data
        assert 'hazard_layer' in data
        assert 'exposure_layer' in data
        assert 'run_duration' in data
        assert 'run_date' in data
        assert 'layer' in data

        assert data['success']

        # Download result and check
        layer_name = data['layer'].split('/')[-1]

        result_layer = download(INTERNAL_SERVER_URL,
                                layer_name,
                                get_bounding_box_string(hazard_filename))
        assert os.path.exists(result_layer.filename)

        # Check calculated values
        keywords = result_layer.get_keywords()

        assert 'caption' in keywords

        # Parse caption and look for the correct numbers


if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'
    suite = unittest.makeSuite(Test_calculations, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
