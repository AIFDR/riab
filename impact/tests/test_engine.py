import unittest
import numpy
import sys
import os

from impact.engine.core import calculate_impact
from impact.engine.interpolation import raster_spline
from impact.storage.io import read_layer

from impact.storage.utilities import unique_filename
from impact.storage.io import write_vector_data
from impact.storage.io import write_raster_data
from impact.plugins import get_plugins

from impact.tests.utilities import TESTDATA


def linear_function(x, y):
    """Auxiliary function for use with interpolation test
    """

    return x + y / 2.0


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


class Test_Engine(unittest.TestCase):

    def test_earthquake_fatality_estimation_allen(self):
        """Fatalities from ground shaking can be computed correctly 1
           using aligned rasters
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = '%s/Earthquake_Ground_Shaking_clip.tif' % TESTDATA
        exposure_filename = '%s/Population_2010_clip.tif' % TESTDATA

        # Calculate impact using API
        H = read_layer(hazard_filename)
        E = read_layer(exposure_filename)

        plugin_name = 'Earthquake Fatality Function'
        plugin_list = get_plugins(plugin_name)
        assert len(plugin_list) == 1
        assert plugin_list[0].keys()[0] == plugin_name

        IF = plugin_list[0][plugin_name]

        # Call calculation engine
        impact_filename = calculate_impact(layers=[H, E],
                                           impact_fcn=IF)

        # Do calculation manually and check result
        hazard_raster = read_layer(hazard_filename)
        H = hazard_raster.get_data(nan=0)

        exposure_raster = read_layer(exposure_filename)
        E = exposure_raster.get_data(nan=0)

        # Calculate impact manually
        a = 0.97429
        b = 11.037
        F = 10 ** (a * H - b) * E

        # Verify correctness of result
        calculated_raster = read_layer(impact_filename)
        C = calculated_raster.get_data(nan=0)

        # Compare shape and extrema
        msg = ('Shape of calculated raster differs from reference raster: '
               'C=%s, F=%s' % (C.shape, F.shape))
        assert numpy.allclose(C.shape, F.shape, rtol=1e-12, atol=1e-12), msg

        msg = ('Minimum of calculated raster differs from reference raster: '
               'C=%s, F=%s' % (numpy.min(C), numpy.min(F)))
        assert numpy.allclose(numpy.min(C), numpy.min(F),
                              rtol=1e-12, atol=1e-12), msg
        msg = ('Maximum of calculated raster differs from reference raster: '
               'C=%s, F=%s' % (numpy.max(C), numpy.max(F)))
        assert numpy.allclose(numpy.max(C), numpy.max(F),
                              rtol=1e-12, atol=1e-12), msg

        # Compare every single value numerically
        msg = 'Array values of written raster array were not as expected'
        assert numpy.allclose(C, F, rtol=1e-12, atol=1e-12), msg

        # Check that extrema are in range
        xmin, xmax = calculated_raster.get_extrema()
        assert numpy.alltrue(C >= xmin)
        assert numpy.alltrue(C <= xmax)
        assert numpy.alltrue(C >= 0)

    def test_earthquake_fatality_estimation_ghasemi(self):
        """Fatalities from ground shaking can be computed correctly 2
           using the Hadi Ghasemi function.
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = '%s/Earthquake_Ground_Shaking_clip.tif' % TESTDATA
        exposure_filename = '%s/Population_2010_clip.tif' % TESTDATA

        # Calculate impact using API
        H = read_layer(hazard_filename)
        E = read_layer(exposure_filename)

        plugin_name = 'Empirical Fatality Function'
        plugin_list = get_plugins(plugin_name)
        assert len(plugin_list) == 1
        assert plugin_list[0].keys()[0] == plugin_name

        IF = plugin_list[0][plugin_name]

        # Call calculation engine
        impact_filename = calculate_impact(layers=[H, E],
                                           impact_fcn=IF)

        # Do calculation manually and check result
        hazard_raster = read_layer(hazard_filename)
        H = hazard_raster.get_data(nan=0)

        exposure_raster = read_layer(exposure_filename)
        E = exposure_raster.get_data(nan=0)

        # Verify correctness of result
        calculated_raster = read_layer(impact_filename)
        C = calculated_raster.get_data(nan=0)

        # Calculate impact manually
        # FIXME (Ole): Jono will do this
        return

        # Compare shape and extrema
        msg = ('Shape of calculated raster differs from reference raster: '
               'C=%s, F=%s' % (C.shape, F.shape))
        assert numpy.allclose(C.shape, F.shape, rtol=1e-12, atol=1e-12), msg

        msg = ('Minimum of calculated raster differs from reference raster: '
               'C=%s, F=%s' % (numpy.min(C), numpy.min(F)))
        assert numpy.allclose(numpy.min(C), numpy.min(F),
                              rtol=1e-12, atol=1e-12), msg
        msg = ('Maximum of calculated raster differs from reference raster: '
               'C=%s, F=%s' % (numpy.max(C), numpy.max(F)))
        assert numpy.allclose(numpy.max(C), numpy.max(F),
                              rtol=1e-12, atol=1e-12), msg

        # Compare every single value numerically
        msg = 'Array values of written raster array were not as expected'
        assert numpy.allclose(C, F, rtol=1e-12, atol=1e-12), msg

        # Check that extrema are in range
        xmin, xmax = calculated_raster.get_extrema()
        assert numpy.alltrue(C >= xmin)
        assert numpy.alltrue(C <= xmax)
        assert numpy.alltrue(C >= 0)

    def test_jakarta_flood_study(self):
        """HKV Jakarta flood study calculated correctly using aligned rasters
        """

        # FIXME (Ole): Redo with population as shapefile later

        # Name file names for hazard level, exposure and expected fatalities

        population = 'Population_Jakarta_geographic.asc'
        plugin_name = 'Flood Impact Function'

        # Expected values from HKV
        expected_values = [2485442, 1537920]

        i = 0
        for filename in ['Flood_Current_Depth_Jakarta_geographic.asc',
                         'Flood_Design_Depth_Jakarta_geographic.asc']:

            hazard_filename = os.path.join(TESTDATA, filename)
            exposure_filename = os.path.join(TESTDATA, population)

            # Get layers using API
            H = read_layer(hazard_filename)
            E = read_layer(exposure_filename)

            plugin_list = get_plugins(plugin_name)
            assert len(plugin_list) == 1
            assert plugin_list[0].keys()[0] == plugin_name

            IF = plugin_list[0][plugin_name]

            # Call impact calculation engine
            impact_filename = calculate_impact(layers=[H, E],
                                               impact_fcn=IF)

            # Do calculation manually and check result
            hazard_raster = read_layer(hazard_filename)
            H = hazard_raster.get_data(nan=0)

            exposure_raster = read_layer(exposure_filename)
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
            calculated_raster = read_layer(impact_filename)
            C = calculated_raster.get_data(nan=0)

            # Check caption
            caption = calculated_raster.get_caption()
            expct = 'people'
            msg = ('Caption %s did not contain expected '
                   'keyword %s' % (caption, expct))
            assert expct in caption, msg

            # Compare shape and extrema
            msg = ('Shape of calculated raster differs from reference raster: '
                   'C=%s, I=%s' % (C.shape, I.shape))
            assert numpy.allclose(C.shape, I.shape,
                                  rtol=1e-12, atol=1e-12), msg

            msg = ('Minimum of calculated raster differs from reference '
                   'raster: '
                   'C=%s, I=%s' % (numpy.min(C), numpy.min(I)))
            assert numpy.allclose(numpy.min(C), numpy.min(I),
                                  rtol=1e-12, atol=1e-12), msg
            msg = ('Maximum of calculated raster differs from reference '
                   'raster: '
                   'C=%s, I=%s' % (numpy.max(C), numpy.max(I)))
            assert numpy.allclose(numpy.max(C), numpy.max(I),
                                  rtol=1e-12, atol=1e-12), msg

            # Compare every single value numerically
            msg = 'Array values of written raster array were not as expected'
            assert numpy.allclose(C, I, rtol=1e-12, atol=1e-12), msg

            # Check that extrema are in range
            xmin, xmax = calculated_raster.get_extrema()
            assert numpy.alltrue(C >= xmin)
            assert numpy.alltrue(C <= xmax)
            assert numpy.alltrue(C >= 0)

            i += 1

    def test_earthquake_damage_schools(self):
        """Lembang building damage from ground shaking works

        This test also exercises ineterpolation of hazard level (raster) to
        building locations (vector data).
        """

        for mmi_filename in ['lembang_mmi_hazmap.asc',
                             'Earthquake_Ground_Shaking_clip.tif',  # NaN's
                             'Lembang_Earthquake_Scenario.asc']:

            # Name file names for hazard level and exposure
            hazard_filename = '%s/%s' % (TESTDATA, mmi_filename)
            exposure_filename = '%s/lembang_schools.shp' % TESTDATA

            # Calculate impact using API
            H = read_layer(hazard_filename)
            E = read_layer(exposure_filename)

            plugin_name = 'Earthquake Building Damage Function'
            plugin_list = get_plugins(plugin_name)
            assert len(plugin_list) == 1
            assert plugin_list[0].keys()[0] == plugin_name

            IF = plugin_list[0][plugin_name]

            impact_filename = calculate_impact(layers=[H, E],
                                               impact_fcn=IF)

            # Read input data
            hazard_raster = read_layer(hazard_filename)
            A = hazard_raster.get_data()
            mmi_min, mmi_max = hazard_raster.get_extrema()

            exposure_vector = read_layer(exposure_filename)
            coordinates = exposure_vector.get_geometry()
            attributes = exposure_vector.get_data()

            # Read calculated result
            impact_vector = read_layer(impact_filename)
            icoordinates = impact_vector.get_geometry()
            iattributes = impact_vector.get_data()

            # First check that interpolated MMI was done as expected
            fid = open('%s/lembang_schools_percentage_loss_and_mmi.txt'
                       % TESTDATA)
            reference_points = []
            MMI = []
            DAM = []
            for line in fid.readlines()[1:]:
                fields = line.strip().split(',')

                lon = float(fields[4][1:-1])
                lat = float(fields[3][1:-1])
                mmi = float(fields[-1][1:-1])
                dam = float(fields[-2][1:-1])

                reference_points.append((lon, lat))
                MMI.append(mmi)
                DAM.append(dam)

            # Verify that coordinates are consistent
            msg = 'Interpolated coordinates do not match those of test data'
            assert numpy.allclose(icoordinates, reference_points), msg

            # Verify interpolated MMI with test result
            min_damage = sys.maxint
            max_damage = -min_damage
            for i in range(len(MMI)):
                lon, lat = icoordinates[i][:]
                calculated_mmi = iattributes[i]['MMI']

                if numpy.isnan(calculated_mmi):
                    continue

                # Check that interpolated points are within range
                msg = ('Interpolated mmi %f from file %s was outside '
                       'extrema: [%f, %f] at location '
                       '[%f, %f].' % (calculated_mmi, hazard_filename,
                                      mmi_min, mmi_max, lon, lat))
                assert mmi_min <= calculated_mmi <= mmi_max, msg

                # Set up some tolerances. Revise when NaN interpolation works
                if mmi_filename.startswith('Lembang_Earthquake'):
                    pct = 10
                else:
                    pct = 2

                # Check that interpolated result is within specified tolerance
                msg = ('Calculated MMI %f deviated more than %.1f%% from '
                       'what was expected %f' % (calculated_mmi, pct, MMI[i]))
                assert numpy.allclose(calculated_mmi, MMI[i],
                                      rtol=float(pct) / 100), msg

                calculated_dam = iattributes[i]['DAMAGE']
                if calculated_dam > max_damage:
                    max_damage = calculated_dam

                if calculated_dam < min_damage:
                    min_damage = calculated_dam

                ref_dam = lembang_damage_function(calculated_mmi)
                msg = ('Calculated damage was not as expected')
                assert numpy.allclose(calculated_dam, ref_dam,
                                      rtol=1.0e-12), msg

                # Test that test data is correct by calculating damage based
                # on reference MMI.
                # FIXME (Ole): UNCOMMENT WHEN WE GET THE CORRECT DATASET
                #expected_test_damage = lembang_damage_function(MMI[i])
                #msg = ('Test data is inconsistent: i = %i, MMI = %f,'
                #       'expected_test_damage = %f, '
                #       'actual_test_damage = %f' % (i, MMI[i],
                #                                    expected_test_damage,
                #                                    DAM[i]))
                #if not numpy.allclose(expected_test_damage,
                #                      DAM[i], rtol=1.0e-12):
                #    print msg

                # Note this test doesn't work, but the question is whether the
                # independent test data is correct.
                # Also small fluctuations in MMI can cause very large changes
                # in computed damage for this example.
                # print mmi, MMI[i], calculated_damage, DAM[i]
                #msg = ('Calculated damage was not as expected for point %i:'
                #       'Got %f, expected %f' % (i, calculated_dam, DAM[i]))
                #assert numpy.allclose(calculated_dam, DAM[i], rtol=0.8), msg

            assert min_damage >= 0
            assert max_damage <= 100
            #print 'Extrema', mmi_filename, min_damage, max_damage
            #print len(MMI)

    def test_tsunami_loss_use_case(self):
        """Building loss from tsunami use case works
        """

        from impact.plugins.tsunami import NEXIS_building_impact_model
        # This test merely exercises the use case as there is
        # no reference data. It does check the sanity of values as
        # far as possible.

        hazard_filename = ('%s/tsunami_max_inundation_depth_BB_'
                           'geographic.asc' % TESTDATA)
        exposure_filename = ('%s/tsunami_exposure_BB.shp' % TESTDATA)
        exposure_with_depth_filename = ('%s/tsunami_exposure_BB_'
                                        'with_depth.shp' % TESTDATA)
        reference_impact_filename = ('%s/tsunami_impact_assessment_'
                                     'BB.shp' % TESTDATA)

        # Calculate impact using API
        H = read_layer(hazard_filename)
        E = read_layer(exposure_filename)

        plugin_name = 'Tsunami Building Loss Function'
        plugin_list = get_plugins(plugin_name)
        assert len(plugin_list) == 1
        assert plugin_list[0].keys()[0] == plugin_name

        IF = plugin_list[0][plugin_name]
        impact_filename = calculate_impact(layers=[H, E],
                                           impact_fcn=IF)

        # Read calculated result
        impact_vector = read_layer(impact_filename)
        icoordinates = impact_vector.get_geometry()
        iattributes = impact_vector.get_data()
        N = len(icoordinates)

        # Ensure that calculated point locations coincide with
        # original exposure point locations
        ref_exp = read_layer(exposure_filename)
        refcoordinates = ref_exp.get_geometry()

        assert N == len(refcoordinates)
        msg = ('Coordinates of impact results do not match those of '
               'exposure data')
        assert numpy.allclose(icoordinates, refcoordinates), msg

        # Ensure that calculated point locations coincide with
        # original exposure point (with depth) locations
        ref_depth = read_layer(exposure_with_depth_filename)
        refdepth_coordinates = ref_depth.get_geometry()
        refdepth_attributes = ref_depth.get_data()
        assert N == len(refdepth_coordinates)
        msg = ('Coordinates of impact results do not match those of '
               'exposure data (with depth)')
        assert numpy.allclose(icoordinates, refdepth_coordinates), msg

        # Read reference results
        hazard_raster = read_layer(hazard_filename)
        A = hazard_raster.get_data()
        depth_min, depth_max = hazard_raster.get_extrema()

        ref_impact = read_layer(reference_impact_filename)
        refimpact_coordinates = ref_impact.get_geometry()
        refimpact_attributes = ref_impact.get_data()

        # Check for None
        for i in range(N):
            if refimpact_attributes[i] is None:
                msg = 'Element %i was None' % i
                raise Exception(msg)

        # Check sanity of calculated attributes
        for i in range(N):
            lon, lat = icoordinates[i]

            depth = iattributes[i]['DEPTH']

            # Ignore NaN's
            if numpy.isnan(depth):
                continue

            structural_damage = iattributes[i]['STRUCT_DAM']
            contents_damage = iattributes[i]['CONTENTS_D']
            for imp in [structural_damage, contents_damage]:
                msg = ('Percent damage was outside range: %f' % imp)
                assert 0 <= imp <= 1, msg

            structural_loss = iattributes[i]['STRUCT_LOS']
            contents_loss = iattributes[i]['CONTENTS_L']
            if depth < 0.3:
                assert structural_loss == 0.0
                assert contents_loss == 0.0
            else:
                assert structural_loss > 0.0
                assert contents_loss > 0.0

            number_of_people = iattributes[i]['NEXIS_PEOP']
            people_affected = iattributes[i]['PEOPLE_AFF']
            people_severely_affected = iattributes[i]['PEOPLE_SEV']

            if 0.01 < depth < 1.0:
                assert people_affected == number_of_people
            else:
                assert people_affected == 0

            if depth >= 1.0:
                assert people_severely_affected == number_of_people
            else:
                assert people_severely_affected == 0

            # Contents and structural damage is done according
            # to different damage curves and should therefore be different
            if depth > 0 and contents_damage > 0:
                assert contents_damage != structural_damage

    def test_tephra_load_impact(self):
        """Hypothetical tephra load scenario can be computed

        This test also exercises reprojection of UTM data
        """

        # File names for hazard level and exposure

        # FIXME - when we know how to reproject, replace hazard
        # file with UTM version (i.e. without _geographic).
        hazard_filename = os.path.join(TESTDATA,
                                       'Ashload_Gede_VEI4_geographic.asc')
        exposure_filename = os.path.join(TESTDATA, 'lembang_schools.shp')

        # Calculate impact using API
        H = read_layer(hazard_filename)
        E = read_layer(exposure_filename)

        plugin_name = 'Tephra Impact Function'
        plugin_list = get_plugins(plugin_name)
        assert len(plugin_list) == 1
        assert plugin_list[0].keys()[0] == plugin_name

        IF = plugin_list[0][plugin_name]
        impact_filename = calculate_impact(layers=[H, E],
                                           impact_fcn=IF)

        # Read input data
        hazard_raster = read_layer(hazard_filename)
        A = hazard_raster.get_data()
        load_min, load_max = hazard_raster.get_extrema()

        exposure_vector = read_layer(exposure_filename)
        coordinates = exposure_vector.get_geometry()
        attributes = exposure_vector.get_data()

        # Read calculated result
        impact_vector = read_layer(impact_filename)
        coordinates = impact_vector.get_geometry()
        attributes = impact_vector.get_data()

        # FIXME: Remove this tolerance when interpolation is better (issue #19)
        tol = 1.0e-8

        # Test that results are as expected
        # FIXME: Change test when we decide what values should actually be
        #        calculated :-) :-) :-)
        for a in attributes:
            load = a['ASHLOAD']
            impact = a['DAMAGE']

            # Test interpolation
            msg = 'Load %.15f was outside bounds [%f, %f]' % (load,
                                                           load_min,
                                                           load_max)
            if not numpy.isnan(load):
                assert load_min - tol <= load <= load_max, msg

            # Test calcalated values
            if 0.01 <= load < 90.0:
                assert impact == 25
            elif 90.0 <= load < 150.0:
                assert impact == 50
            elif 150.0 <= load < 300.0:
                assert impact == 75
            elif load >= 300.0:
                assert impact == 100
            else:
                assert impact == 0

    def test_package_metadata(self):
        """Test that riab package loads
        """

        import impact

        impact.VERSION
        impact.__version__
        impact.__author__
        impact.__contact__
        impact.__homepage__
        impact.__docformat__
        assert impact.__license__ == 'GPL'

    def test_interpolation_wrapper(self):
        """Interpolation library works for linear function
        """

        # Create test data
        lon_ul = 100  # Longitude of upper left corner
        lat_ul = 10   # Latitude of upper left corner
        numlon = 8    # Number of longitudes
        numlat = 5    # Number of latitudes
        dlon = 1
        dlat = -1

        # Define array where latitudes are rows and longitude columns
        A = numpy.zeros((numlat, numlon))

        # Establish coordinates for lower left corner
        lat_ll = lat_ul - numlat
        lon_ll = lon_ul

        # Define pixel centers along each direction
        longitudes = numpy.linspace(lon_ll + 0.5,
                                    lon_ll + numlon - 0.5, numlon)
        latitudes = numpy.linspace(lat_ll + 0.5,
                                   lat_ll + numlat - 0.5, numlat)

        # Define raster with latitudes going bottom-up (south to north).
        # Longitudes go left-right (west to east)
        for i in range(numlat):
            for j in range(numlon):
                A[numlat - 1 - i, j] = linear_function(longitudes[j],
                                                   latitudes[i])

        # Create bilinear interpolation function
        F = raster_spline(longitudes, latitudes, A)

        # Test first that original points are reproduced correctly
        for i, eta in enumerate(latitudes):
            for j, xi in enumerate(longitudes):
                assert numpy.allclose(F(xi, eta),
                                      linear_function(xi, eta),
                                      rtol=1e-12, atol=1e-12)

        # Then test that genuinly interpolated points are correct
        xis = numpy.linspace(lon_ll + 1, lon_ll + numlon - 1, 10 * numlon)
        etas = numpy.linspace(lat_ll + 1, lat_ll + numlat - 1, 10 * numlat)
        for xi in xis:
            for eta in etas:
                assert numpy.allclose(F(xi, eta),
                                      linear_function(xi, eta),
                                      rtol=1e-12, atol=1e-12)

        # FIXME (Ole): Need test for values outside grid.
        #              They should be NaN or something

    def test_riab_interpolation(self):
        """Interpolation using Raster and Vector objects
        """

        # Create test data
        lon_ul = 100  # Longitude of upper left corner
        lat_ul = 10   # Latitude of upper left corner
        numlon = 8    # Number of longitudes
        numlat = 5    # Number of latitudes
        dlon = 1
        dlat = -1

        # Define array where latitudes are rows and longitude columns
        A = numpy.zeros((numlat, numlon))

        # Establish coordinates for lower left corner
        lat_ll = lat_ul - numlat
        lon_ll = lon_ul

        # Define pixel centers along each direction
        longitudes = numpy.linspace(lon_ll + 0.5,
                                    lon_ll + numlon - 0.5,
                                    numlon)
        latitudes = numpy.linspace(lat_ll + 0.5,
                                   lat_ll + numlat - 0.5,
                                   numlat)

        # Define raster with latitudes going bottom-up (south to north).
        # Longitudes go left-right (west to east)
        for i in range(numlat):
            for j in range(numlon):
                A[numlat - 1 - i, j] = linear_function(longitudes[j],
                                                       latitudes[i])

        # Create bilinear interpolation function
        F = raster_spline(longitudes, latitudes, A)

        # Write array to a raster file
        geotransform = (lon_ul, dlon, 0, lat_ul, 0, dlat)
        projection = ('GEOGCS["GCS_WGS_1984",'
                      'DATUM["WGS_1984",'
                      'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
                      'PRIMEM["Greenwich",0.0],'
                      'UNIT["Degree",0.0174532925199433]]')

        raster_filename = unique_filename(suffix='.tif')
        write_raster_data(A,
                          projection,
                          geotransform,
                          raster_filename)

        # Write test interpolation point to a vector file
        coordinates = []
        for xi in longitudes:
            for eta in latitudes:
                coordinates.append((xi, eta))

        vector_filename = unique_filename(suffix='.shp')
        write_vector_data(data=None,
                          projection=projection,
                          geometry=coordinates,
                          filename=vector_filename)

        # Read both datasets back in
        R = read_layer(raster_filename)
        V = read_layer(vector_filename)

        # Then test that axes and data returned by R are correct
        x, y = R.get_geometry()
        msg = 'X axes was %s, should have been %s' % (longitudes, x)
        assert numpy.allclose(longitudes, x), msg
        msg = 'Y axes was %s, should have been %s' % (latitudes, y)
        assert numpy.allclose(latitudes, y), msg
        AA = R.get_data()
        msg = 'Raster data was %s, should have been %s' % (AA, A)
        assert numpy.allclose(AA, A), msg

        # Test riab's interpolation function
        I = R.interpolate(V, name='value')
        Icoordinates = I.get_geometry()
        Iattributes = I.get_data()

        assert numpy.allclose(Icoordinates, coordinates)

        # Test that interpolated points are correct
        for i, (xi, eta) in enumerate(Icoordinates):

            z = Iattributes[i]['value']
            #print xi, eta, z, linear_function(xi, eta)
            assert numpy.allclose(z, linear_function(xi, eta),
                                  rtol=1e-12)

        # FIXME (Ole): Need test for values outside grid.
        #              They should be NaN or something

        # Cleanup
        # FIXME (Ole): Shape files are a collection of files. How to remove?
        os.remove(vector_filename)

    def test_interpolation_lembang(self):
        """Interpolation using Lembang data set
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = '%s/lembang_mmi_hazmap.asc' % TESTDATA
        exposure_filename = '%s/lembang_schools.shp' % TESTDATA

        # Read input data
        hazard_raster = read_layer(hazard_filename)
        A = hazard_raster.get_data()
        mmi_min, mmi_max = hazard_raster.get_extrema()

        exposure_vector = read_layer(exposure_filename)
        coordinates = exposure_vector.get_geometry()
        attributes = exposure_vector.get_data()

        # Test riab's interpolation function
        I = hazard_raster.interpolate(exposure_vector,
                                      name='mmi')
        Icoordinates = I.get_geometry()
        Iattributes = I.get_data()
        assert numpy.allclose(Icoordinates, coordinates)

        # Check that interpolated MMI was done as expected
        fid = open('%s/lembang_schools_percentage_loss_and_mmi.txt' % TESTDATA)
        reference_points = []
        MMI = []
        DAM = []
        for line in fid.readlines()[1:]:
            fields = line.strip().split(',')

            lon = float(fields[4][1:-1])
            lat = float(fields[3][1:-1])
            mmi = float(fields[-1][1:-1])

            reference_points.append((lon, lat))
            MMI.append(mmi)

        # Verify that coordinates are consistent
        msg = 'Interpolated coordinates do not match those of test data'
        assert numpy.allclose(Icoordinates, reference_points), msg

        # Verify interpolated MMI with test result
        for i in range(len(MMI)):
            calculated_mmi = Iattributes[i]['mmi']

            # Check that interpolated points are within range
            msg = ('Interpolated mmi %f was outside extrema: '
                   '[%f, %f]. ' % (calculated_mmi, mmi_min, mmi_max))
            assert mmi_min <= calculated_mmi <= mmi_max, msg

            # Check that result is within 2% - this is good enough
            # as this was calculated using EQRM and thus different.
            assert numpy.allclose(calculated_mmi, MMI[i], rtol=0.02)

    # FIXME (Ole): Disabled until we get onto the
    # new interpolation scheme (issue #19)
    def Xtest_interpolation_tsunami(self):
        """Interpolation using tsunami data set
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = ('%s/tsunami_max_inundation_depth_BB_'
                           'geographic.asc' % TESTDATA)
        exposure_filename = ('%s/tsunami_exposure_BB.shp' % TESTDATA)

        # Read input data
        hazard_raster = read_layer(hazard_filename)
        A = hazard_raster.get_data()
        depth_min, depth_max = hazard_raster.get_extrema()

        exposure_vector = read_layer(exposure_filename)
        coordinates = exposure_vector.get_geometry()
        attributes = exposure_vector.get_data()

        # Test riab's interpolation function
        I = hazard_raster.interpolate(exposure_vector,
                                      name='depth')
        Icoordinates = I.get_geometry()
        Iattributes = I.get_data()
        assert numpy.allclose(Icoordinates, coordinates)

        # Verify interpolated values with test result
        for i in range(len(Icoordinates)):

            interpolated_depth = Iattributes[i]['depth']
            # Check that interpolated points are within range
            msg = ('Interpolated depth %f at point %i was outside extrema: '
                   '[%f, %f]. ' % (interpolated_depth, i,
                                   depth_min, depth_max))

            if not numpy.isnan(interpolated_depth):
                tol = 1.0e-6
                assert depth_min - tol <= interpolated_depth <= depth_max, msg

    # FIXME (Ole): This is another test for interpolation. Work in progress.
    # Enable when workning on issue #19
    def Xtest_interpolation_tsunami_maumere(self):
        """Interpolation using tsunami data set from Maumere

        This data showed some very wrong results from interpolation overshoot
        when first attempted in August 2011 - hence this test
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = ('%s/maumere_aos_depth_20m_land_wgs84.asc'
                           % TESTDATA)
        exposure_filename = ('%s/maumere_pop_prj.shp' % TESTDATA)

        # Read input data
        H = read_layer(hazard_filename)
        A = H.get_data()
        depth_min, depth_max = H.get_extrema()

        # Compare extrema to values read off QGIS for this layer
        assert numpy.allclose([depth_min, depth_max], [0.0, 16.68],
                              rtol=1.0e-6, atol=1.0e-10)

        E = read_layer(exposure_filename)
        coordinates = E.get_geometry()
        attributes = E.get_data()

        # Test riab's interpolation function
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

                #print i, pointid, attributes[i],
                #print interpolated_depth, coordinates[i]

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
                assert depth_min - tol <= interpolated_depth <= depth_max, msg


if __name__ == '__main__':
    suite = unittest.makeSuite(Test_Engine, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
