import os
from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

os.environ["DJANGO_SETTINGS_MODULE"] = "risiko.settings"
application = WSGIHandler()
