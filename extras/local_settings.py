import os

DEBUG = False
#DEBUG = True

SERVER_IP="http://demo.riskinabox.org"

PROJECT_HOME="/home/software"
SITEURL="%s/" % SERVER_IP
GEOSERVER_BASE_URL="%s/geoserver-geonode-dev/" % SERVER_IP
GEONETWORK_BASE_URL="%s/geonetwork/" % SERVER_IP
MEDIA_ROOT = os.path.join(PROJECT_HOME, 'static')
STATIC_ROOT= MEDIA_ROOT
MEDIA_URL = "/media/"
STATIC_URL = MEDIA_URL
GEONODE_CLIENT_LOCATION = MEDIA_URL + "geonode/"
ADMIN_MEDIA_PREFIX = MEDIA_URL + "admin/"

# This key works for demo.riskinabox.org
GOOGLE_API_KEY="ABQIAAAAC7wlIZDRK6Oon88pViNfRRQ_mqcryycL5Nm40t3UsHGXnKbk7hStK8jHoORRBSPpXKFZ66cYUdvpZA"

import logging
for _module in ["geonode.maps.views", "geonode.maps.gs_helpers"]:
    _logger = logging.getLogger(_module)
    _logger.addHandler(logging.FileHandler(os.path.join(PROJECT_HOME, 'logs', 'geonode.log')))
    # available levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
    # The earlier a level appears in this list, the more output it will produce in the log file.
    _logger.setLevel(logging.WARNING)
