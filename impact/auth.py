"""Module to manage user authentication

Wraps GeoNode's user management for Risiko purposes
"""

from django.contrib.auth.models import User
from geonode.maps.utils import get_default_user


def create_risiko_superuser():
    """Create default superuser for risiko
    """

    username = 'admin'
    userpass = 'risiko'
    user, _ = User.objects.get_or_create(username=username,
                                         defaults={'password': userpass,
                                                   'is_superuser': True})
    return user


def get_guaranteed_valid_user(user=None):
    """Get specified user.

    If it is anonymous create and return default superuser.
    Note, this would not be safe in a public web service, but
    is OK for locally running Risiko applications.
    """

    if user is None:
        theuser = get_default_user()
    elif isinstance(user, basestring):
        theuser = User.objects.get(username=user)
    elif user.is_anonymous():
        theuser = create_risiko_superuser()
    else:
        theuser = request.user

    return theuser
