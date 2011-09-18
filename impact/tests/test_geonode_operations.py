from geonode.maps.utils import upload, GeoNodeException
from geonode.maps.models import Layer
from impact.storage.utilities import unique_filename, LAYER_TYPES
from impact.storage.io import get_bounding_box
from impact.storage.io import download, get_metadata
from django.conf import settings
import os
import time
import unittest
import numpy
import urllib2
from geonode.maps.utils import get_valid_user
from impact.storage.io import save_to_geonode, RisikoException
from impact.storage.io import check_layer, assert_bounding_box_matches
from impact.storage.io import get_bounding_box_string
from impact.tests.utilities import TESTDATA, INTERNAL_SERVER_URL
from impact.tests.utilities import get_web_page
from impact.storage.io import read_layer

#---Jeff
from owslib.wcs import WebCoverageService
import tempfile


# FIXME: Can go when OWSLib patch comes on line
def ns(tag):
    return '{http://www.opengis.net/wcs}' + tag
#---


class Test_geonode_connection(unittest.TestCase):
    """Tests file uploads, metadata etc
    """

    def setUp(self):
        """Create valid superuser
        """
        self.user = get_valid_user()

    def tearDown(self):
        pass

    def test_layer_upload(self):
        """Layers can be uploaded to local GeoNode
        """

        expected_layers = []
        not_expected_layers = []
        datadir = TESTDATA
        BAD_LAYERS = ['grid_without_projection.asc',
                      'kecamatan_prj.shp']  # FIXME(Ole): This layer is not
                                            # 'BAD', just in a different
                                            # projection (TM3_Zone_48-2) so
                                            # serves as another test for
                                            # issue #40

        for root, dirs, files in os.walk(datadir):
            for filename in files:
                basename, extension = os.path.splitext(filename)

                if extension.lower() in LAYER_TYPES:
                    # FIXME(Ole): GeoNode converts names to lower case
                    name = unicode(basename.lower())
                    if filename in BAD_LAYERS:
                        not_expected_layers.append(name)
                    else:
                        expected_layers.append(name)

        # Upload
        layers = save_to_geonode(datadir, user=self.user, overwrite=True,
                                 ignore=BAD_LAYERS)

        # Check integrity
        layer_names = [l.name for l in layers]
        for layer in layers:
            msg = 'Layer %s was uploaded but not expected' % layer.name
            assert layer.name in expected_layers, msg

            # Uncomment to reproduce issue #102
            # This may still also reproduce issue #40 for layer
            # tsunami_max_inundation_depth_bb_utm
            #check_layer(layer, full=True)

        for layer_name in expected_layers:
            msg = ('The following layer should have been uploaded '
                   'but was not: %s' % layer_name)
            assert layer_name in layer_names, msg

            # Check the layer is in the Django database
            Layer.objects.get(name=layer_name)

            # Check that layer is in geoserver
            found = False
            gs_username, gs_password = settings.GEOSERVER_CREDENTIALS
            page = get_web_page(os.path.join(settings.GEOSERVER_BASE_URL,
                                             'rest/layers'),
                                             username=gs_username,
                                             password=gs_password)
            for line in page:
                if line.find('rest/layers/%s.html' % layer_name) > 0:
                    found = True
            if not found:
                msg = ('Upload could not be verified, the layer %s is not '
                   'in geoserver %s, but GeoNode did not raise any errors, '
                   'this should never happen.' %
                   (layer_name, settings.GEOSERVER_BASE_URL))
                raise GeoNodeException(msg)

        server_url = settings.GEOSERVER_BASE_URL + 'ows?'

        # Verify that the GeoServer GetCapabilities record is accessible:
        metadata = get_metadata(server_url)
        msg = ('The metadata list should not be empty in server %s'
                % server_url)
        assert len(metadata) > 0, msg

        # FIXME(Ole): Check the keywords are recognized too

    def test_raster_wcs_reprojection(self):
        """UTM Raster can be reprojected by Geoserver and downloaded correctly
        """
        # FIXME (Ole): Still need to do this with assertions

        filename = 'tsunami_max_inundation_depth_BB_utm.asc'
        projected_tif_file = os.path.join(TESTDATA, filename)

        #projected_tif = file_upload(projected_tif_file, overwrite=True)
        projected_tif = save_to_geonode(projected_tif_file,
                                        user=self.user,
                                        overwrite=True)
        check_layer(projected_tif)

        wcs_url = settings.GEOSERVER_BASE_URL + 'wcs'
        wcs = WebCoverageService(wcs_url, version='1.0.0')
        #logger.info(wcs.contents)
        metadata = wcs.contents[projected_tif.typename]
        #logger.info(metadata.grid)
        bboxWGS84 = metadata.boundingBoxWGS84
        #logger.info(bboxWGS84)
        resx = metadata.grid.offsetvectors[0][0]
        resy = abs(float(metadata.grid.offsetvectors[1][1]))
        #logger.info("resx=%s resy=%s" % (str(resx), str(resy)))
        formats = metadata.supportedFormats
        #logger.info(formats)
        supportedCRS = metadata.supportedCRS
        #logger.info(supportedCRS)
        width = metadata.grid.highlimits[0]
        height = metadata.grid.highlimits[1]
        #logger.info("width=%s height=%s" % (width, height))
        gs_cat = Layer.objects.gs_catalog
        cvg_store = gs_cat.get_store(projected_tif.name)
        cvg_layer = gs_cat.get_resource(projected_tif.name, store=cvg_store)
        #logger.info(cvg_layer.request_srs_list)
        #logger.info(cvg_layer.response_srs_list)

        # FIXME: A patch was submitted OWSlib 20110808
        # Can delete the following once patch appears
        # In the future get bboxNative and nativeSRS from get_metadata
        descCov = metadata._service.getDescribeCoverage(projected_tif.typename)
        envelope = (descCov.find(ns('CoverageOffering/') + ns('domainSet/') +
                                 ns('spatialDomain/') +
                                 '{http://www.opengis.net/gml}Envelope'))
        nativeSrs = envelope.attrib['srsName']
        #logger.info(nativeSrs)
        gmlpositions = envelope.findall('{http://www.opengis.net/gml}pos')
        lc = gmlpositions[0].text
        uc = gmlpositions[1].text
        bboxNative = (float(lc.split()[0]), float(lc.split()[1]),
                      float(uc.split()[0]), float(uc.split()[1]))
        #logger.info(bboxNative)
        # ---- END PATCH

        # Make a temp dir to store the saved files
        tempdir = '/tmp/%s' % str(time.time())
        os.mkdir(tempdir)

        # Check that the layer can be downloaded in its native projection
        cvg = wcs.getCoverage(identifier=projected_tif.typename,
                format='GeoTIFF',
                crs=nativeSrs,
                bbox=bboxNative,
                resx=resx,
                resy=resy)

        t = tempfile.NamedTemporaryFile(delete=False,
                                        dir=tempdir)

        out = open(t.name, 'wb')
        out.write(cvg.read())
        out.close()
        #logger.info("GeoTIFF in %s = %s" % (nativeSrs, t.name))
        # TODO: Verify that the file is a valid GeoTiff and that it is
        # _exactly_ the same size and bbox of the original

        # Test that the layer can be downloaded in ARCGRID format
        cvg_layer.supported_formats = cvg_layer.supported_formats + ['ARCGRID']
        gs_cat.save(cvg_layer)
        cvg = wcs.getCoverage(identifier=projected_tif.typename,
                format='ARCGRID',
                crs=nativeSrs,
                bbox=bboxNative,
                resx=resx,
                resy=resy)

        t = tempfile.NamedTemporaryFile(delete=False,
                                    dir=tempdir)

        out = open(t.name, 'wb')
        out.write(cvg.read())
        out.close()
        #logger.info("ARCGRID in %s = %s" % (nativeSrs, t.name))
        # Check that the downloaded file is a valid ARCGRID file and that it
        # the required projection information
        # (FIXME: There is no prj file here. GS bug)

        # Check that the layer can downloaded in WGS84
        cvg_layer.request_srs_list += ['EPSG:4326']
        cvg_layer.response_srs_list += ['EPSG:4326']
        gs_cat.save(cvg_layer)
        #logger.info(cvg_layer.request_srs_list)
        #logger.info(cvg_layer.response_srs_list)
        cvg = wcs.getCoverage(identifier=projected_tif.typename,
                format='GeoTIFF',
                crs='EPSG:4326',
                bbox=bboxWGS84,
                #resx=0.000202220898116, # Should NOT be hard-coded!
                                         # How do we convert
                #resy=0.000202220898116) # See comments in riab issue #103
                width=width,
                height=height)

        t = tempfile.NamedTemporaryFile(delete=False,
                                    dir=tempdir)

        out = open(t.name, 'wb')
        out.write(cvg.read())
        out.close()
        #logger.info("GeoTIFF in %s = %s" % ("EPSG:4326", t.name))
        # TODO: Verify that the file is a valid GeoTiff and that it is
        # the correct size and bbox based on the resx and resy or width
        # and height specified

        # Check that we can download the layer in another projection
        cvg_layer.request_srs_list += ['EPSG:32356']
        cvg_layer.response_srs_list += ['EPSG:32356']
        cvg_layer.request_srs_list += ['EPSG:900913']
        cvg_layer.response_srs_list += ['EPSG:900913']
        gs_cat.save(cvg_layer)
        #logger.info(cvg_layer.request_srs_list)
        #logger.info(cvg_layer.response_srs_list)
        # How do we get the bboxes for the newly assigned
        # request/response SRS??

        cvg = wcs.getCoverage(identifier=projected_tif.typename,
                format='GeoTIFF',
                crs='EPSG:32356',  # Should not be hardcoded for a test,
                                   # or should use 900913 (need bbox)
                bbox=bboxNative,
                #resx=0.000202220898116, # Should NOT be hard-coded!
                                         # How do we convert
                #resy=0.000202220898116) # See comments in riab issue #103
                width=width,
                height=height)

        t = tempfile.NamedTemporaryFile(delete=False,
                                        dir=tempdir)

        out = open(t.name, 'wb')
        out.write(cvg.read())
        out.close()
        #logger.info("GeoTIFF in %s = %s" % ("EPSG:32356", t.name))
        # TODO: Verify that the file is a valid GeoTiff and that it is
        # the correct size and bbox based on the resx and resy or width
        # and height specified

        # Clean up and completely delete the layer
        #projected_tif.delete()

    def test_extension_not_implemented(self):
        """RisikoException is returned for not compatible extensions
        """
        sampletxt = os.path.join(TESTDATA,
                                 'lembang_schools_percentage_loss.dbf')
        try:
            save_to_geonode(sampletxt, user=self.user)
        except RisikoException, e:
            pass
        else:
            msg = ('Expected an exception for invalid .dbf type')
            raise Exception(msg)

    def test_shapefile(self):
        """Shapefile can be uploaded
        """
        thefile = os.path.join(TESTDATA, 'lembang_schools.shp')
        layer = save_to_geonode(thefile, user=self.user, overwrite=True)
        check_layer(layer, full=True)

        assert isinstance(layer.geographic_bounding_box, basestring)

    def test_shapefile_without_prj(self):
        """Shapefile with without prj file is rejected
        """

        thefile = os.path.join(TESTDATA,
                               'lembang_schools_percentage_loss.shp')
        try:
            uploaded = save_to_geonode(thefile, user=self.user)
        except RisikoException, e:
            pass
        except Exception, e:
            msg = ('Was expecting a %s, got %s instead.' %
                   (RisikoException, type(e)))
            assert e is RisikoException, msg

    def test_asciifile_without_prj(self):
        """ASCII file with without prj file is rejected
        """

        thefile = os.path.join(TESTDATA,
                               'grid_without_projection.asc')

        try:
            uploaded = save_to_geonode(thefile, user=self.user)
        except RisikoException, e:
            pass
        except Exception, e:
            msg = ('Was expecting a %s, got %s instead.' %
                   (RisikoException, type(e)))
            assert e is RisikoException, msg

    def test_tiff(self):
        """GeoTIF file can be uploaded
        """
        thefile = os.path.join(TESTDATA, 'Population_2010_clip.tif')
        uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)
        check_layer(uploaded, full=True)

    def test_asc(self):
        """ASCII file can be uploaded
        """
        thefile = os.path.join(TESTDATA, 'test_grid.asc')
        uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)
        check_layer(uploaded, full=True)

    def test_another_asc(self):
        """Real world ASCII file can be uploaded
        """
        thefile = os.path.join(TESTDATA, 'lembang_mmi_hazmap.asc')
        layer = save_to_geonode(thefile, user=self.user, overwrite=True)
        check_layer(layer, full=True)

        # Verify metadata
        layer_name = '%s:%s' % (layer.workspace, layer.name)
        metadata = get_metadata(INTERNAL_SERVER_URL,
                                layer_name)
        assert 'id' in metadata
        assert 'title' in metadata
        assert 'layer_type' in metadata
        assert 'keywords' in metadata
        assert 'bounding_box' in metadata
        assert 'geotransform' in metadata
        assert len(metadata['bounding_box']) == 4

        # A little metadata characterisation test
        ref = {'layer_type': 'raster',
               'keywords': {'category': 'hazard',
                            'subcategory': 'earthquake'},
               'geotransform': (105.29857, 0.0112, 0.0,
                                -5.565233000000001, 0.0, -0.0112),
               'title': 'lembang_mmi_hazmap'}

        for key in ['layer_type', 'keywords', 'geotransform',
                    'title']:

            msg = ('Expected metadata for key %s to be %s. '
                   'Instead got %s' % (key, ref[key], metadata[key]))
            if key == 'geotransform':
                assert numpy.allclose(metadata[key], ref[key]), msg
            else:
                assert metadata[key] == ref[key], msg

            if key == 'keywords':
                kwds = metadata[key]
                for k in kwds:
                    assert kwds[k] == ref[key][k]

    def test_repeated_upload(self):
        """The same file can be uploaded more than once
        """
        thefile = os.path.join(TESTDATA, 'test_grid.asc')
        uploaded1 = save_to_geonode(thefile, overwrite=True,
                                    user=self.user)
        check_layer(uploaded1, full=True)
        uploaded2 = save_to_geonode(thefile, overwrite=True,
                                    user=self.user)
        check_layer(uploaded2, full=True)
        uploaded3 = save_to_geonode(thefile, overwrite=False,
                                    user=self.user)
        check_layer(uploaded3, full=True)

        msg = ('Expected %s but got %s' % (uploaded1.name, uploaded2.name))
        assert uploaded1.name == uploaded2.name, msg

        msg = ('Expected a different name when uploading %s using '
               'overwrite=False but got %s' % (thefile, uploaded3.name))
        assert uploaded1.name != uploaded3.name, msg

    def test_layer_name_validation(self):
        """Exception is raised when get_valid_layer_name is given a time object
        """
        from geonode.maps.utils import get_valid_layer_name
        import datetime
        try:
            get_valid_layer_name(datetime.datetime.now())
        except GeoNodeException, e:
            pass
        else:
            msg = ('Get_valid_layer_name accepted a time'
                   ' object and did not complain')
            assert False, msg

    def test_non_existing_file(self):
        """RisikoException is returned for non existing file
        """
        sampletxt = os.path.join(TESTDATA, 'smoothoperator.shp')
        try:
            save_to_geonode(sampletxt, user=self.user)
        except RisikoException, e:
            pass
        else:
            msg = ('Expected an exception for non existing file')
            assert False, msg

    def test_non_existing_dir(self):
        """RisikoException is returned for non existing dir
        """
        sampletxt = os.path.join(TESTDATA, 'smoothoperator')
        try:
            uploaded_layers = save_to_geonode(sampletxt, user=self.user)
            for uploaded in uploaded_layers:
                print uploaded
        except RisikoException, e:
            pass
        else:
            msg = ('Expected an exception for non existing dir')
            assert False, msg

    def test_cleanup(self):
        """Cleanup functions in the utils module work
        """
        from geonode.maps.utils import cleanup

        thefile = os.path.join(TESTDATA, 'lembang_mmi_hazmap.asc')
        uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)
        check_layer(uploaded, full=True)

        name = uploaded.name
        uuid = uploaded.uuid
        pk = uploaded.pk

        # try calling the cleanup function when the django record exists:
        try:
            cleanup(name, uuid)
        except GeoNodeException, e:
            pass
        else:
            msg = ('Cleaup should raise an exception if the layer [%s]'
                   ' exists in the django db' % name)
            assert False, msg

        # Manually delete the layer object with SQL
        from django.db import connection, transaction
        cursor = connection.cursor()
        cursor.execute('DELETE FROM maps_layer WHERE id = %d' % pk)
        transaction.commit_unless_managed()

        # After this, the records should not live in GeoServer or Geonetwork
        cleanup(name, uuid)

        #FIXME: Verify the record does not exist in GS or GN

    def test_keywords(self):
        """Keywords are read correctly from the .keywords file
        """

        for filename in ['Earthquake_Ground_Shaking.asc',
                         'Lembang_Earthquake_Scenario.asc',
                         'Padang_WGS84.shp']:

            _, ext = os.path.splitext(filename)
            thefile = os.path.join(TESTDATA, filename)
            uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)

            # Get uploaded keywords from uploaded layer object
            uploaded_keywords = uploaded.keywords
            msg = 'No keywords found in layer %s' % uploaded.name
            assert len(uploaded_keywords) > 0, msg

            # Get reference keywords from file
            keywords_file = thefile.replace(ext, '.keywords')
            f = open(keywords_file, 'r')
            keywords_list = []
            for line in f.readlines():
                keywords_list.append(line.strip().replace(' ', ''))
            f.close()

            # Verify that every keyword from file has been uploaded
            for keyword in keywords_list:
                msg = 'Could not find keyword "%s" in %s' % (keyword,
                                                             uploaded_keywords)
                assert keyword in uploaded_keywords, msg

    def test_metadata_twice(self):
        """Layer metadata can be correctly uploaded multiple times
        """

        # This test reproduces ticket #99 by creating new data,
        # uploading twice and verifying metadata

        # Base test data
        filenames = ['Lembang_Earthquake_Scenario.asc',
                     'lembang_schools.shp']

        for org_filename in filenames:
            org_basename, ext = os.path.splitext(os.path.join(TESTDATA,
                                                              org_filename))

            # Copy data to temporary unique name
            basename = unique_filename(dir='/tmp')

            cmd = '/bin/cp %s.keywords %s.keywords' % (org_basename, basename)
            os.system(cmd)

            cmd = '/bin/cp %s.prj %s.prj' % (org_basename, basename)
            os.system(cmd)

            if ext == '.asc':
                layer_type = 'raster'
                filename = '%s.asc' % basename
                cmd = '/bin/cp %s.asc %s' % (org_basename, filename)
                os.system(cmd)
            elif ext == '.shp':
                layer_type = 'vector'
                filename = '%s.shp' % basename
                for e in ['shp', 'shx', 'sbx', 'sbn', 'dbf']:
                    cmd = '/bin/cp %s.%s %s.%s' % (org_basename, e,
                                                   basename, e)
                    os.system(cmd)
            else:
                msg = ('Unknown layer extension in %s. '
                       'Expected .shp or .asc' % filename)
                raise Exception(msg)

            # Repeat multiple times
            for i in range(3):

                # Upload
                layer = save_to_geonode(filename, user=self.user,
                                        overwrite=True)

                # Get metadata
                layer_name = '%s:%s' % (layer.workspace, layer.name)
                metadata = get_metadata(INTERNAL_SERVER_URL,
                                        layer_name)

                # Verify
                assert 'id' in metadata
                assert 'title' in metadata
                assert 'layer_type' in metadata
                assert 'keywords' in metadata
                assert 'bounding_box' in metadata
                assert len(metadata['bounding_box']) == 4

                # Check integrity between Django layer and file
                assert_bounding_box_matches(layer, filename)

                # Check integrity between file and OWS metadata
                ref_bbox = get_bounding_box(filename)
                msg = ('Bounding box from OWS did not match bounding box '
                       'from file. They are\n'
                       'From file %s: %s\n'
                       'From OWS: %s' % (filename,
                                         ref_bbox,
                                         metadata['bounding_box']))

                assert numpy.allclose(metadata['bounding_box'],
                                      ref_bbox), msg
                assert layer.name == metadata['title']
                assert layer_name == metadata['id']
                assert layer_type == metadata['layer_type']

                # Check keywords
                if layer_type == 'raster':
                    category = 'hazard'
                    subcategory = 'earthquake'
                elif layer_type == 'vector':
                    category = 'exposure'
                    subcategory = 'building'
                else:
                    msg = 'Unknown layer type %s' % layer_type
                    raise Exception(msg)

                keywords = metadata['keywords']

                msg = 'Did not find key "category" in keywords: %s' % keywords
                assert 'category' in keywords, msg

                msg = ('Did not find key "subcategory" in keywords: %s'
                       % keywords)
                assert 'subcategory' in keywords, msg

                msg = ('Category keyword %s did not match expected %s'
                       % (keywords['category'], category))
                assert category == keywords['category'], msg

                msg = ('Subcategory keyword %s did not match expected %s'
                       % (keywords['subcategory'], category))
                assert subcategory == keywords['subcategory'], msg

    def test_metadata(self):
        """Metadata is retrieved correctly for both raster and vector data
        """

        # Upload test data
        filenames = ['Lembang_Earthquake_Scenario.asc',
                     'Earthquake_Ground_Shaking.asc',
                     'lembang_schools.shp',
                     'Padang_WGS84.shp']
        layers = []
        paths = []
        for filename in filenames:
            basename, ext = os.path.splitext(filename)

            path = os.path.join(TESTDATA, filename)
            layer = save_to_geonode(path, user=self.user, overwrite=True)

            # Record layer and file
            layers.append(layer)
            paths.append(path)

        # Check integrity
        for i, layer in enumerate(layers):

            if filenames[i].endswith('.shp'):
                layer_type = 'vector'
            elif filenames[i].endswith('.asc'):
                layer_type = 'raster'
            else:
                msg = ('Unknown layer extension in %s. '
                       'Expected .shp or .asc' % filenames[i])
                raise Exception(msg)

            layer_name = '%s:%s' % (layer.workspace, layer.name)
            metadata = get_metadata(INTERNAL_SERVER_URL,
                                    layer_name)

            assert 'id' in metadata
            assert 'title' in metadata
            assert 'layer_type' in metadata
            assert 'keywords' in metadata
            assert 'bounding_box' in metadata
            assert len(metadata['bounding_box']) == 4

            # Check integrity between Django layer and file
            assert_bounding_box_matches(layer, paths[i])

            # Check integrity between file and OWS metadata
            ref_bbox = get_bounding_box(paths[i])
            msg = ('Bounding box from OWS did not match bounding box '
                   'from file. They are\n'
                   'From file %s: %s\n'
                   'From OWS: %s' % (paths[i],
                                     ref_bbox,
                                     metadata['bounding_box']))

            assert numpy.allclose(metadata['bounding_box'],
                                  ref_bbox), msg
            assert layer.name == metadata['title']
            assert layer_name == metadata['id']
            assert layer_type == metadata['layer_type']

            # Check keywords
            if layer_type == 'raster':
                category = 'hazard'
                subcategory = 'earthquake'
            elif layer_type == 'vector':
                category = 'exposure'
                subcategory = 'building'
            else:
                msg = 'Unknown layer type %s' % layer_type
                raise Exception(msg)

            keywords = metadata['keywords']

            msg = 'Did not find key "category" in keywords: %s' % keywords
            assert 'category' in keywords, msg

            msg = 'Did not find key "subcategory" in keywords: %s' % keywords
            assert 'subcategory' in keywords, msg

            msg = ('Category keyword %s did not match expected %s'
                   % (keywords['category'], category))
            assert category == keywords['category'], msg

            msg = ('Subcategory keyword %s did not match expected %s'
                   % (keywords['subcategory'], category))
            assert subcategory == keywords['subcategory'], msg

    # FIXME (Ole): Enable when issue #103 has been resolved
    def Xtest_raster_upload(self):
        """Raster layer can be uploaded and downloaded again correctly
        """

        hazard_filename = ('%s/maumere_aos_depth_20m_land_wgs84.asc'
                           % TESTDATA)

        # Get reference values
        H = read_layer(hazard_filename)
        A_ref = H.get_data()
        depth_min_ref, depth_max_ref = H.get_extrema()

        # Upload to internal geonode
        hazard_layer = save_to_geonode(hazard_filename, user=self.user)
        hazard_name = '%s:%s' % (hazard_layer.workspace, hazard_layer.name)

        # Download data again
        bbox = get_bounding_box_string(hazard_filename)
        H = download(INTERNAL_SERVER_URL, hazard_name, bbox)
        A = H.get_data()

        # Compare shapes
        msg = ('Shape of downloaded raster was [%i, %i]. '
               'Expected [%i, %i].' % (A.shape[0], A.shape[1],
                                       A_ref.shape[0], A_ref.shape[1]))
        assert numpy.allclose(A_ref.shape, A.shape, rtol=0, atol=0), msg

        # Compare extrema to values reference values (which have also been
        # verified by QGIS for this layer and tested in test_engine.py)
        depth_min, depth_max = H.get_extrema()
        msg = ('Extrema of downloaded file were [%f, %f] but '
               'expected [%f, %f]' % (depth_min, depth_max,
                                      depth_min_ref, depth_max_ref))
        assert numpy.allclose([depth_min, depth_max],
                              [depth_min_ref, depth_max_ref],
                              rtol=1.0e-6, atol=1.0e-10), msg

        # FIXME (Ole): Eventually compare number by number
        #assert numpy.allclose(A, A_ref)


if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'
    suite = unittest.makeSuite(Test_geonode_connection, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
