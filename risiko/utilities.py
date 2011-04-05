from geonode.maps.utils import upload

def save_to_geonode(filename, user, title):
    """Saves a calculation from Risk In a Box in GeoNode
    """
    layer = upload(filename, user, title, overwrite=False)
    return layer.get_absolute_url()
