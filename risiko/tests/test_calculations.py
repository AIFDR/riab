from geonode.maps.utils import upload, file_upload, GeoNodeException
from django.conf import settings
from impact.views import calculate

import os
import unittest

TEST_DATA = os.path.join(os.environ['RIAB_HOME'],
                         'riab_data', 'risiko_test_data')



class Test_calculations(unittest.TestCase):
    """Tests of Risiko calculations
    """

    def test_school_example(self):
        """Test building earthquake impact calculation
        """

        # Upload input data
        hazardfile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        uploaded = file_upload(hazardfile)

        exposurefile = os.path.join(TEST_DATA, 'lembang_schools.shp')
        uploaded = file_upload(exposurefile)


        # Call calculation routine




if __name__ == '__main__':
    import logging

    os.environ["DJANGO_SETTINGS_MODULE"] = "risiko.settings"

    # Set up logging
    for _module in ['geonode.maps.utils']:
        _logger = logging.getLogger(_module)
        _logger.addHandler(logging.StreamHandler())
        # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        _logger.setLevel(logging.CRITICAL)

    suite = unittest.makeSuite(Test_calculations, 'test')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

