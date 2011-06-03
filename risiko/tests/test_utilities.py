from geonode.maps.utils import upload, GeoNodeException
from geonode.maps.models import Layer
from impact.storage.utilities import get_layers_metadata, LAYER_TYPES
from impact.storage.io import download
from django.conf import settings
import os
import unittest
import urllib2
from geonode.maps.utils import get_valid_user
from risiko.utilities import save_to_geonode, RisikoException

TEST_DATA = os.path.join(os.environ['RIAB_HOME'],
                         'riab_data', 'risiko_test_data')


def check_layer(uploaded):
    """Verify if an object is a valid Layer.
    """

    msg = ('Was expecting layer object, got %s' % (type(uploaded)))
    assert type(uploaded) is Layer, msg
    msg = ('The layer does not have a valid name: %s' % uploaded.name)
    assert len(uploaded.name) > 0, msg

    # Check that layer can be downloaded
    #print dir(uploaded)
    #print 'name', uploaded.name
    #print 'url', uploaded.get_absolute_url()
    #print 'bbox', uploaded.geographic_bounding_box
    #download(server_url, layer_name, bbox)


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
        datadir = TEST_DATA
        BAD_LAYERS = ['grid_without_projection.asc']

        for root, dirs, files in os.walk(datadir):
            for filename in files:
                basename, extension = os.path.splitext(filename)

                if extension.lower() in LAYER_TYPES:

                    # FIXME(Ole): GeoNode converts names to lower case
                    name = unicode(basename.lower())
                    if filename not in BAD_LAYERS:
                        expected_layers.append(name)
                    else:
                        not_expected_layers.append(name)

        # Upload
        layers = save_to_geonode(datadir, user=self.user, overwrite=True)

        # Check integrity
        layer_names = [l.name for l in layers]

        for layer in layers:
            msg = 'Layer %s was uploaded but not expected' % layer.name
            assert layer.name in expected_layers, msg

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

        # Verify that the GeoServer GetCapabilities record is accesible:
        metadata = get_layers_metadata(server_url, '1.0.0')
        msg = ('The metadata list should not be empty in server %s'
                % server_url)
        assert len(metadata) > 0, msg

        # FIXME(Ole): Check the keywords are recognized too

    def test_extension_not_implemented(self):
        """RisikoException is returned for not compatible extensions
        """
        sampletxt = os.path.join(TEST_DATA,
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
        thefile = os.path.join(TEST_DATA, 'lembang_schools.shp')
        uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)
        check_layer(uploaded)

    def test_shapefile_without_prj(self):
        """Shapefile with without prj file is rejected
        """

        thefile = os.path.join(TEST_DATA,
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

        thefile = os.path.join(TEST_DATA,
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
        thefile = os.path.join(TEST_DATA, 'Population_2010_clip.tif')
        uploaded = save_to_geonode(thefile, user=self.user)
        check_layer(uploaded)

    def test_asc(self):
        """ASCII file can be uploaded
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.asc')
        uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)
        check_layer(uploaded)

    def test_another_asc(self):
        """Real world ASCII file can be uploaded
        """
        thefile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.asc')
        layer = save_to_geonode(thefile, user=self.user)
        check_layer(layer)

    def test_repeated_upload(self):
        """The same file can be uploaded more than once
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.asc')
        uploaded1 = save_to_geonode(thefile, overwrite=True,
                                    user=self.user)
        check_layer(uploaded1)
        uploaded2 = save_to_geonode(thefile, overwrite=True,
                                    user=self.user)
        check_layer(uploaded2)
        uploaded3 = save_to_geonode(thefile, overwrite=False,
                                    user=self.user)
        check_layer(uploaded3)
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
        sampletxt = os.path.join(TEST_DATA, 'smoothoperator.shp')
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
        sampletxt = os.path.join(TEST_DATA, 'smoothoperator')
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

        thefile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.asc')
        uploaded = save_to_geonode(thefile, user=self.user)
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
        """Check that keywords are read from the .keywords file
        """
        thefile = os.path.join(TEST_DATA, 'Lembang_Earthquake_Scenario.asc')
        uploaded = save_to_geonode(thefile, user=self.user, overwrite=True)

        keywords = uploaded.keywords
        msg = 'No keywords found in layer %s' % uploaded.name
        assert len(keywords) > 0, msg

        keywords_file = thefile.replace('.asc', '.keywords')
        f = open(keywords_file, 'r')
        keywords_list = []
        for line in f.readlines():
            keywords_list.append(line.strip())
        f.close()

        for keyword in keywords_list:
            msg = 'Could not find keyword "%s" in %s' % (keyword,
                                                         keywords_list)
            assert keyword in keywords_list, msg

if __name__ == '__main__':
    os.environ['DJANGO_SETTINGS_MODULE'] = 'risiko.settings'
    suite = unittest.makeSuite(Test_utilities, 'test_keywords')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
