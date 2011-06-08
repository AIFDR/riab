import os

#DEBUG = False
DEBUG = True


PROJECT_HOME = '%(riab_home)s'
SITEURL = 'http://%(host)s/'
GEOSERVER_BASE_URL = 'http://%(host)s/geoserver-geonode-dev/'
GEONETWORK_BASE_URL = 'http://%(host)s/geonetwork/'

# This key works for demo.riskinabox.org
GOOGLE_API_KEY = 'ABQIAAAAC7wlIZDRK6Oon88pViNfRRQ_mqcryycL5Nm40t3UsHGXnKbk7hStK8jHoORRBSPpXKFZ66cYUdvpZA'

# Added this here because mod_wsgi did not seem to like django_nose
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django_extensions',
    'registration',
    'profiles',
    'avatar',
    'geonode.core',
    'geonode.maps',
    'geonode.proxy',
    'impact',
    'rosetta',
)

