from geonode.maps.utils import file_upload


def save_to_geonode(filename, user, title):
    """Saves a calculation from Risk In a Box in GeoNode
    """
    layer = file_upload(filename, user=user, title=title, overwrite=False)
    return layer.get_absolute_url()
