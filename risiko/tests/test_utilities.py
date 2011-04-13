from geonode.maps.utils import upload, file_upload, GeoNodeException
from geonode.maps.models import Layer
from impact.storage.utilities import get_layers_metadata
from django.conf import settings
import os
import unittest
import urllib2

TEST_DATA = os.path.join(os.environ['RIAB_HOME'],
                       'riab_data', 'risiko_test_data')

def check_layer(uploaded):
    """Verify if an object is a valid Layer.
    """
    msg = ('Was expecting layer object, got %s' % (type(uploaded)))
    assert type(uploaded) is Layer, msg
    msg = ('The layer does not have a valid name: %s' % uploaded.name)
    assert len(uploaded.name) > 0, msg


def get_web_page(url, username=None, password=None):
    """Get url page possible with username and password.
    """

    if username is not None:

        # Create password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        # create the handler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    try:
        pagehandle = urllib2.urlopen(url)
    except HTTPError, e:
        msg = ('The server couldn\'t fulfill the request. '
                'Error code: ' % e.code)
        e.args = (msg,)
        raise
    except urllib2.URLError, e:
        msg = 'Could not open URL "%s": %s' % (url, e)
        e.args = (msg,)
        raise
    else:
        page = pagehandle.readlines()

    return page


class Test_utilities(unittest.TestCase):
    """Tests riab_geonode utilities
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """
        layers = {}
        expected_layers = []
        not_expected_layers = []
        datadir = TEST_DATA
        BAD_LAYERS = [
            'lembang_schools_percentage_loss.shp',
        ]

        for filename in os.listdir(datadir):
            basename, extension = os.path.splitext(filename)
            if extension.lower() in ['.asc', '.tif', '.shp', '.zip']:
                if filename not in BAD_LAYERS:
                    expected_layers.append(os.path.join(datadir, filename))
                else:
                    not_expected_layers.append(
                                    os.path.join(datadir, filename)
                                             )
        uploaded = upload(datadir)

        for item in uploaded:
            errors = 'errors' in item
            if errors:
                # should this file have been uploaded?
                if item['file'] in not_expected_layers:
                    continue
                msg = 'Could not upload %s. ' % item['file']
                assert errors is False, msg + 'Error was: %s' % item['errors']
                msg = ('Upload should have returned either "name" or '
                  '"errors" for file %s.' % item['file'])
            else:
                assert 'name' in item, msg
                layers[item['file']] = item['name']

        msg = ('There were %s compatible layers in the directory,'
               ' but only %s were sucessfully uploaded' %
               (len(expected_layers), len(layers)))
        assert len(layers) == len(expected_layers), msg

        uploaded_layers = [layer for layer in layers.items()]

        for layer in expected_layers:
            msg = ('The following file should have been uploaded'
                   'but was not: %s. ' % layer)
            assert layer in layers, msg

            layer_name = layers[layer]

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
        # Verify that the GeoServer GetCapabilities record is accesible:
        metadata = get_layers_metadata(server_url, '1.0.0')
        msg = ('The metadata list should not be empty in server %s'
                % server_url)
        assert len(metadata) > 0, msg
        # Check the keywords are recognized too

    def test_extension_not_implemented(self):
        """Verify a GeoNodeException is returned for not compatible extensions
        """
        sampletxt = os.path.join(TEST_DATA, 'lembang_schools_percentage_loss.dbf')
        try:
            file_upload(sampletxt)
        except GeoNodeException, e:
            pass
        else:
            msg = ('Expected an exception for invalid .dbf type')
            assert False, msg


    def test_shapefile(self):
        """Uploading a good shapefile
        """
        thefile = os.path.join(TEST_DATA, 'lembang_schools.shp')
        uploaded = file_upload(thefile)
        check_layer(uploaded)


    def test_bad_shapefile(self):
        """Verifying GeoNode complains about a shapefile without .prj
        """

        thefile = os.path.join(TEST_DATA, 'lembang_schools_percentage_loss.shp')
        try:
            uploaded = file_upload(thefile)
        except GeoNodeException, e:
            pass
        except Exception, e:
            msg = ('Was expecting a %s, got %s instead.' %
                   (GeoNodeException, type(e)))
            assert e is GeoNodeException, msg


    def test_tiff(self):
        """Uploading a good tiff
        """
        thefile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        uploaded = file_upload(thefile)
        check_layer(uploaded)


    def test_asc(self):
        """Uploading a good .asc
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.asc')
        uploaded = file_upload(thefile)
        check_layer(uploaded)


    def test_repeated_upload(self):
        """Upload the same file more than once
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.asc')
        uploaded1 = file_upload(thefile)
        check_layer(uploaded1)
        uploaded2 = file_upload(thefile, overwrite=True)
        check_layer(uploaded2)
        uploaded3 = file_upload(thefile, overwrite=False)
        check_layer(uploaded3)
        msg = ('Expected %s but got %s' % (uploaded1.name, uploaded2.name))
        assert uploaded1.name == uploaded2.name, msg
        msg = ('Expected a different name when uploading %s using '
               'overwrite=False but got %s' % (thefile, uploaded3.name))
        assert uploaded1.name != uploaded3.name, msg

    def test_layer_name_validation(self):
        """Test get_valid_layer_name utility function in corner cases
        """
        from geonode.maps.utils import get_valid_layer_name
        import datetime
        try:
            get_valid_layer_name(datetime.datetime.now())
        except GeoNodeException, e:
            pass
        else:
            msg = 'get_valid_layer_name accepted a time object and did not complain'
            assert False, msg


    def test_non_existing_file(self):
        """Verify a GeoNodeException is returned for not existing file
        """
        sampletxt = os.path.join(TEST_DATA, 'smoothoperator.shp')
        try:
            file_upload(sampletxt)
        except GeoNodeException, e:
            pass
        else:
            msg = ('Expected an exception for non existing file')
            assert False, msg

    def test_non_existing_dir(self):
        """Verify a GeoNodeException is returned for not existing dir
        """
        sampletxt = os.path.join(TEST_DATA, 'smoothoperator')
        try:
            uploaded_files = upload(sampletxt)
            for uploaded in uploaded_files:
                print uploaded
        except GeoNodeException, e:
            pass
        else:
            msg = ('Expected an exception for non existing dir')
            assert False, msg


    def test_single_file_batch(self):
        """Test single file using batch upload function
        """
        thefile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        uploaded_files = upload(thefile)
        i = 0
        for uploaded in uploaded_files:
            layer = Layer.objects.get(name=uploaded['name'])
            check_layer(layer)
            i += 1
        msg = ('Only one file was expected and got %d' % i)
        assert i == 1, msg


    def test_cleanup(self):
        """Test the cleanup functions in the utils module
        """
        from geonode.maps.utils import cleanup

        thefile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        uploaded = file_upload(thefile)
        check_layer(uploaded)

        name = uploaded.name
        uuid = uploaded.uuid
        pk = uploaded.pk

        # try calling the cleanup function when the django record exists:
        try:
            cleanup(name, uuid)
        except GeoNodeException, e:
            pass
        else:
            msg = ('Cleaup should raise an exception if the layer [%s] exists in the django db' % name)
            assert False, msg

        # Manually delete the layer object with SQL
        from django.db import connection, transaction
        cursor = connection.cursor()
        cursor.execute('DELETE FROM maps_layer WHERE id= %d' % pk)
        transaction.commit_unless_managed()

        # After this, the records should not live in GeoServer or Geonetwork
        cleanup(name, uuid)

        #FIXME: Verify the record does not exist in GS or GN

if __name__ == '__main__':
    import logging

    os.environ["DJANGO_SETTINGS_MODULE"] = "risiko.settings"

    # Set up logging
    for _module in ['geonode.maps.utils']:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler())
        # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        _logger.setLevel(logging.WARNING)

    suite = unittest.makeSuite(Test_utilities, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
