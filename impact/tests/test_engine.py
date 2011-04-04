import unittest
import numpy
import sys
import os

import riab_server
from utilities import TESTDATA


def linear_function(x, y):
    """Auxiliary function for use with interpolation test
    """

    return x + y / 2.


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

    def test_earthquake_fatality_estimation(self):
        """Test that fatalities from ground shaking can be computed correctly
           using aligned rasters
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = '%s/Earthquake_Ground_Shaking_clip.tif' % TESTDATA
        exposure_filename = '%s/Population_2010_clip.tif' % TESTDATA

        # Calculate impact using API
        HD = riab_server.read_layer(hazard_filename)
        ED = riab_server.read_layer(exposure_filename)

        IF = riab_server.get_function('EarthquakeFatalityFunction')
        impact_filename = riab_server.calculate_impact(hazard_level=HD,
                                                       exposure_level=ED,
                                                       impact_function=IF)

        # Do calculation manually and check result
        hazard_raster = riab_server.read_layer(hazard_filename)
        H = hazard_raster.get_data()

        exposure_raster = riab_server.read_layer(exposure_filename)
        E = exposure_raster.get_data()

        # Calculate impact manually
        a = 0.97429
        b = 11.037
        F = 10 ** (a * H - b) * E

        # Verify correctness of result
        calculated_raster = riab_server.read_layer(impact_filename)
        C = calculated_raster.get_data()

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

        # Check that extrema are in range (except for ESRI ASCII NODATA)
        if numpy.min(C) < 0:
            assert numpy.min(E) == -9999

    def test_earthquake_damage_schools(self):
        """Test (school) building damage from ground shaking

        This test also exercises ineterpolation of hazard level (raster) to
        building locations (vector data).
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = '%s/lembang_mmi_hazmap.asc' % TESTDATA
        exposure_filename = '%s/lembang_schools.shp' % TESTDATA

        # Calculate impact using API
        HD = riab_server.read_layer(hazard_filename)
        ED = riab_server.read_layer(exposure_filename)

        IF = riab_server.get_function('EarthquakeSchoolDamageFunction')
        impact_filename = riab_server.calculate_impact(hazard_level=HD,
                                                       exposure_level=ED,
                                                       impact_function=IF)

        # Read input data
        hazard_raster = riab_server.read_layer(hazard_filename)
        A = hazard_raster.get_data()
        mmi_min, mmi_max = hazard_raster.get_extrema()

        exposure_vector = riab_server.read_layer(exposure_filename)
        coordinates, attributes = exposure_vector.get_data()

        # Read calculated result
        impact_vector = riab_server.read_layer(impact_filename)
        icoordinates, iattributes = impact_vector.get_data()

        # First check that interpolated MMI was done as expected
        fid = open('%s/lembang_schools_percentage_loss_and_mmi.txt' % TESTDATA)
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
        print
        for i in range(len(MMI)):
            #print i, iattributes[i]
            calculated_mmi = iattributes[i]['MMI']

            # Check that interpolated points are within range
            msg = ('Interpolated mmi %f was outside extrema: '
                   '[%f, %f]. ' % (calculated_mmi, mmi_min, mmi_max))
            assert mmi_min <= calculated_mmi <= mmi_max, msg

            # Check that result is within 2%
            msg = ('Calculated MMI deviated more than 2\% from '
                   'what was expected')
            assert numpy.allclose(calculated_mmi, MMI[i], rtol=0.02), msg

            # FIXME (Ole): Has to shorten name to 10 characters
            #              until issue #1 has been resolved.
            calculated_dam = iattributes[i]['Percent_da']
            if calculated_dam > max_damage:
                max_damage = calculated_dam

            if calculated_dam < min_damage:
                min_damage = calculated_dam

            ref_dam = lembang_damage_function(calculated_mmi)
            msg = ('Calculated damage was not as expected')
            assert numpy.allclose(calculated_dam, ref_dam, rtol=1.0e-12), msg

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
        #print 'Extrema', min_damage, max_damage
        #print len(MMI)

    def test_tsunami_loss_use_case(self):
        """Test building loss from tsunami use case
        """

        # This test merely exercises the use case as there is
        # no reference data. It does check the sanity of values as
        # far as possible.

        # FIXME (Ole): Replace this with normal ASCII raster when
        #              NaN interpolation has been sorted out (issue #6)
        hazard_filename = ('%s/tsunami_max_inundation_depth_BB_'
                           'geographic_nan0.asc' % TESTDATA)
        exposure_filename = ('%s/tsunami_exposure_BB.shp' % TESTDATA)
        exposure_with_depth_filename = ('%s/tsunami_exposure_BB_'
                                        'with_depth.shp' % TESTDATA)
        reference_impact_filename = ('%s/tsunami_impact_assessment_'
                                     'BB.shp' % TESTDATA)

        # Calculate impact using API
        HD = riab_server.read_layer(hazard_filename)
        ED = riab_server.read_layer(exposure_filename)

        IF = riab_server.get_function('TsunamiBuildingLossFunction')
        impact_filename = riab_server.calculate_impact(hazard_level=HD,
                                                       exposure_level=ED,
                                                       impact_function=IF)

        # Read calculated result
        impact_vector = riab_server.read_layer(impact_filename)
        icoordinates, iattributes = impact_vector.get_data()
        N = len(icoordinates)

        # Ensure that calculated point locations coincide with
        # original exposure point locations
        ref_exp = riab_server.read_layer(exposure_filename)
        refcoordinates, _ = ref_exp.get_data()

        assert N == len(refcoordinates)
        msg = ('Coordinates of impact results do not match those of '
               'exposure data')
        assert numpy.allclose(icoordinates, refcoordinates), msg

        # Ensure that calculated point locations coincide with
        # original exposure point (with depth) locations
        ref_depth = riab_server.read_layer(exposure_with_depth_filename)
        refdepth_coordinates, refdepth_attributes = ref_depth.get_data()
        assert N == len(refdepth_coordinates)
        msg = ('Coordinates of impact results do not match those of '
               'exposure data (with depth)')
        assert numpy.allclose(icoordinates, refdepth_coordinates), msg

        # Read reference results
        hazard_raster = riab_server.read_layer(hazard_filename)
        A = hazard_raster.get_data()
        depth_min, depth_max = hazard_raster.get_extrema()

        ref_impact = riab_server.read_layer(reference_impact_filename)
        refimpact_coordinates, refimpact_attributes = ref_impact.get_data()

        # Check for None
        for i in range(N):
            if refimpact_attributes[i] is None:
                msg = 'Element %i was None' % i
                raise Exception(msg)

        # Check sanity of calculated attributes
        for i in range(N):
            lon, lat = icoordinates[i, :]

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

    def XXXtest_tsunami_loss_buildings(self):
        """Test building loss from tsunami against reference data
        """

        # FIXME (Ole): This test is stuffed as the reference data
        # was shuffled.

        # FIXME (Ole): Replace this with normal ASCII raster when
        #              NaN interpolation has been sorted out (issue #6)
        hazard_filename = ('%s/tsunami_max_inundation_depth_BB_'
                           'geographic_nan0.asc' % TESTDATA)
        exposure_filename = ('%s/tsunami_exposure_BB.shp' % TESTDATA)
        exposure_with_depth_filename = ('%s/tsunami_exposure_BB_'
                                        'with_depth.shp' % TESTDATA)
        reference_impact_filename = ('%s/tsunami_impact_assessment_'
                                     'BB.shp' % TESTDATA)

        # Calculate impact using API
        HD = hazard_filename
        ED = exposure_filename
        IF = riab_server.get_function('TsunamiBuildingLossFunction')
        impact_filename = riab_server.calculate_impact(hazard_level=HD,
                                                       exposure_level=ED,
                                                       impact_function=IF)

        # Read calculated result
        impact_vector = riab_server.read_layer(impact_filename)
        icoordinates, iattributes = impact_vector.get_data()
        N = len(icoordinates)

        # Ensure that calculated point locations coincide with
        # original exposure point locations
        ref_exp = riab_server.read_layer(exposure_filename)
        refcoordinates, _ = ref_exp.get_data()

        assert N == len(refcoordinates)
        msg = ('Coordinates of impact results do not match those of '
               'exposure data')
        assert numpy.allclose(icoordinates, refcoordinates), msg

        # Ensure that calculated point locations coincide with
        # original exposure point (with depth) locations
        ref_depth = riab_server.read_layer(exposure_with_depth_filename)
        refdepth_coordinates, refdepth_attributes = ref_depth.get_data()
        assert N == len(refdepth_coordinates)
        msg = ('Coordinates of impact results do not match those of '
               'exposure data (with depth)')
        assert numpy.allclose(icoordinates, refdepth_coordinates), msg

        # Read reference results
        hazard_raster = riab_server.read_layer(hazard_filename)
        A = hazard_raster.get_data()
        depth_min, depth_max = hazard_raster.get_extrema()

        ref_impact = riab_server.read_layer(reference_impact_filename)
        refimpact_coordinates, refimpact_attributes = ref_impact.get_data()

        # FIXME (Ole): Reconsider from this point on
        return

        # Read reference data
        import pickle
        try:
            fid = open('tsunami_reference_impact.pkl')
        except:

            # Reference impact data does not use the same order for exposure
            # coordinates and the calculated impact locations :-(
            # Therefore we need to reorder before comparison.

            print
            print 'Reorder reference data and pickle.'
            print 'This will take a while but need only be done once.'
            print 'Have patience.'
            print 'This test will be replaced at a later stage anyway.'
            newrefimpact_coor = numpy.zeros((N, 2))
            newrefimpact_attr = [None] * N
            for i in range(N):
                lon, lat = icoordinates[i, :]
                #print i, N
                for j in range(N):
                    rlon, rlat = refimpact_coordinates[j, :]

                    if lon == rlon and lat == rlat:
                        newrefimpact_coor[i, :] = refimpact_coordinates[j, :]
                        newrefimpact_attr[i] = refimpact_attributes[j]

            refimpact_coordinates = newrefimpact_coor
            refimpact_attributes = newrefimpact_attr

            # Pickle reference data
            import pickle
            fid = open('tsunami_reference_impact.pkl', 'wb')
            pickle.dump((refimpact_coordinates, refimpact_attributes), fid)
            fid.close()
        else:
            #print 'Reading reordered data from pickle'
            refimpact_coordinates, refimpact_attributes = pickle.load(fid)

        # Verify that coordinates are now consistent
        msg = 'Reference data coordinates do not match those calculated'
        assert numpy.allclose(icoordinates, refimpact_coordinates), msg

        for i in range(N):
            if refimpact_attributes[i] is None:
                msg = 'Element %i was None' % i
                raise Exception(msg)

        # Check that interpolated depths are OK
        count = 0
        for i in range(N):
            d = iattributes[i]['DEPTH']
            ref_d = refdepth_attributes[i]['MAX_DEPTH_']

            if numpy.isnan(d):
                continue

            #if d < 0.0:
            #    print d, ref_d

            lon, lat = icoordinates[i, :]
            msg = ('Interpolated depth %f was outside extrema: [%f, %f] at '
                   'location (%f, %f). ' % (d, depth_min, depth_max, lon, lat))
            assert depth_min - 1 <= d <= depth_max, msg

            # Count how many are within a 2% tolerance.
            # Due to the very different sources we can't ask
            # for more here.
            if numpy.allclose(d, ref_d, rtol=1.0e-6, atol=0.06):
                count += 1
            #else:
            #    print i, d, ref_d

        #print count * 100. / N
        msg = 'Less than 90\% of interpolated depth points were outside 2%'
        assert count * 100. / N > 90, msg

        # FIXME: Still issue with field width - see issue #2
        for a in ['PEOPLE_AFF',
                  'PEOPLE_SEV',
                  'STRUCT_INU',
                  'STRUCT_DAM',
                  'CONTENTS_D',
                  'STRUCT_LOS',    # TODO........
                  'CONTENTS_L']:

            count = 0
            #print
            #print a
            for i in range(N):
                lon, lat = icoordinates[i, :]
                imp = iattributes[i][a]
                ref = refimpact_attributes[i][a]

                if numpy.isnan(imp):
                    continue

                if numpy.allclose(imp, ref, rtol=1.0e-2, atol=1.0e-1):
                    count += 1
                #else:
                #    print a, i, lon, lat, imp, ref

            msg = ('Less than 90\% of calculated impact attributes '
                   'were outside 2%')
            assert count * 100. / N > 90, msg

    def test_package_metadata(self):
        """Test that riab package loads
        """

        riab_server.VERSION
        riab_server.__version__
        riab_server.__author__
        riab_server.__contact__
        riab_server.__homepage__
        riab_server.__docformat__
        assert riab_server.__license__ == 'GPL'

    def test_interpolation_wrapper(self):
        """Test underlying interpolation library
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
        F = riab_server.raster_spline(longitudes, latitudes, A)

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
        """Test riabs interpolation using Raster and Vector objects
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
        F = riab_server.raster_spline(longitudes, latitudes, A)

        # Write array to a raster file
        geotransform = (lon_ul, dlon, 0, lat_ul, 0, dlat)
        projection = ('GEOGCS["GCS_WGS_1984",'
                      'DATUM["WGS_1984",'
                      'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
                      'PRIMEM["Greenwich",0.0],'
                      'UNIT["Degree",0.0174532925199433]]')

        raster_filename = riab_server.unique_filename(suffix='.tif')
        riab_server.write_coverage(A,
                                   projection,
                                   geotransform,
                                   raster_filename)

        # Write test interpolation point to a vector file
        coordinates = []
        for xi in longitudes:
            for eta in latitudes:
                coordinates.append((xi, eta))

        vector_filename = riab_server.unique_filename(suffix='.shp')
        riab_server.write_point_data(coordinates, projection, None,
                                   vector_filename)

        # Read both datasets back in
        R = riab_server.read_layer(raster_filename)
        V = riab_server.read_layer(vector_filename)

        # Then test that axes and coveraged returned by R are correct
        x, y = R.get_axes()
        msg = 'X axes was %s, should have been %s' % (longitudes, x)
        assert numpy.allclose(longitudes, x), msg
        msg = 'Y axes was %s, should have been %s' % (latitudes, y)
        assert numpy.allclose(latitudes, y), msg
        AA = R.get_data()
        msg = 'Raster data was %s, should have been %s' % (AA, A)
        assert numpy.allclose(AA, A), msg

        # Test riab's interpolation function
        I = riab_server.interpolate(R, V, name='value')
        Icoordinates, Iattributes = I.get_data()

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
        """Test interpolation using Lembang data set
        """

        # Name file names for hazard level, exposure and expected fatalities
        hazard_filename = '%s/lembang_mmi_hazmap.asc' % TESTDATA
        exposure_filename = '%s/lembang_schools.shp' % TESTDATA

        # Read input data
        hazard_raster = riab_server.read_layer(hazard_filename)
        A = hazard_raster.get_data()
        mmi_min, mmi_max = hazard_raster.get_extrema()

        exposure_vector = riab_server.read_layer(exposure_filename)
        coordinates, attributes = exposure_vector.get_data()

        # Test riab's interpolation function
        I = riab_server.interpolate(hazard_raster, exposure_vector,
                                    name='mmi')
        Icoordinates, Iattributes = I.get_data()
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

    def test_interpolation_tsunami(self):
        """Test interpolation using tsunami data set
        """

        # Name file names for hazard level, exposure and expected fatalities

        # FIXME (Ole): Replace this with normal ASCII raster when
        #              NaN interpolation has been sorted out (issue #6)
        hazard_filename = ('%s/tsunami_max_inundation_depth_BB_'
                           'geographic_nan0.asc' % TESTDATA)
        exposure_filename = ('%s/tsunami_exposure_BB.shp' % TESTDATA)

        # Read input data
        hazard_raster = riab_server.read_layer(hazard_filename)
        A = hazard_raster.get_data()
        depth_min, depth_max = hazard_raster.get_extrema()

        exposure_vector = riab_server.read_layer(exposure_filename)
        coordinates, attributes = exposure_vector.get_data()

        # Test riab's interpolation function
        I = riab_server.interpolate(hazard_raster, exposure_vector,
                                    name='depth')
        Icoordinates, Iattributes = I.get_data()
        assert numpy.allclose(Icoordinates, coordinates)

        # Verify interpolated values with test result
        for i in range(len(Icoordinates)):

            interpolated_depth = Iattributes[i]['depth']
            # Check that interpolated points are within range
            msg = ('Interpolated depth %f at point %i was outside extrema: '
                   '[%f, %f]. ' % (interpolated_depth, i,
                                   depth_min, depth_max))
            assert depth_min <= interpolated_depth <= depth_max, msg

if __name__ == '__main__':
    suite = unittest.makeSuite(Test_Engine, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
