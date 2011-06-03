"""
Risk in a Box HTTP API

All API calls start with:
 http://myriab.com/riab/api/v1

 * Version: All API calls begin with API version.
 * Path: For this documentation, we will assume every
         request begins with the above path.
 * Units: All coordinates are in WGS-84 (EPSG:4326)
          unless otherwise specified and all units of
          measurement are in the International System
          of Units (SI).
 * Format: All calls are returned in JSON.
 * Status Codes:
    200 Successful GET and PUT.
    201 Successful POST.
    202 Successful calculation queued.
    204 Successful DELETE
    401 Unauthenticated.
    409 Unsuccessful POST, PUT, or DELETE
        (Will return an errors object).
"""
from __future__ import division

import inspect
import datetime

from django.utils import simplejson as json
from django.http import HttpResponse
from django.conf import settings

from impact.storage.io import dummy_save, download, get_layers_metadata
from impact.plugins.core import get_plugins, compatible_layers
from impact.engine.core import calculate_impact
from impact.models import Calculation, Workspace

from geonode.maps.utils import get_valid_user

import logging
logger = logging.getLogger('risiko')


def calculate(request, save_output=dummy_save):
    start = datetime.datetime.now()

    if request.method == 'GET':
        # FIXME: Add a basic form here to be able to generate the POST request.
        return HttpResponse('This should be accessed by robots, not humans.'
                            'In other words using HTTP POST instead of GET.')
    elif request.method == 'POST':
        data = request.POST
        impact_function_name = data['impact_function']
        hazard_server = data['hazard_server']
        hazard_layer = data['hazard']
        exposure_server = data['exposure_server']
        exposure_layer = data['exposure']
        bbox = data['bbox']
        keywords = data['keywords']

    if request.user.is_anonymous():
        theuser = get_valid_user()
    else:
        theuser = request.user

    plugin_list = get_plugins(impact_function_name)
    _, impact_function = plugin_list[0].items()[0]
    impact_function_source = inspect.getsource(impact_function)

    # Create entry in database
    calculation = Calculation(user=theuser,
                              run_date=start,
                              hazard_server=hazard_server,
                              hazard_layer=hazard_layer,
                              exposure_server='exposure_server',
                              exposure_layer='exposure_layer',
                              impact_function=impact_function_name,
                              impact_function_source=impact_function_source,
                              bbox=bbox,
                              success=False)
    calculation.save()

    logger.info('Performing requested calculation')
    # Download selected layer objects
    logger.info('- Downloading hazard layer %s from %s' % (hazard_layer,
                                                           hazard_server))
    H = download(hazard_server, hazard_layer, bbox)
    logger.info('- Downloading exposure layer %s from %s' % (exposure_layer,
                                                             exposure_server))
    E = download(exposure_server, exposure_layer, bbox)

    # Calculate result using specified impact function
    logger.info('- Calculating impact using %s' % impact_function)

    impact_filename = calculate_impact(layers=[H, E],
                                       impact_function=impact_function)

    # Upload result to internal GeoServer
    logger.info('- Uploading impact layer %s' % impact_filename)
    result = save_output(impact_filename,
                         title='output_%s' % start.isoformat(),
                         user=theuser)
    logger.info('- Result available at %s.' % result.get_absolute_url())

    calculation.layer = result.get_absolute_url()
    calculation.success = True
    calculation.save()

    output = calculation.__dict__

    # json.dumps does not like datetime objects,
    # let's make it a json string ourselves
    output['run_date'] = 'new Date("%s")' % calculation.run_date

    # FIXME:This should not be needed in an ideal world
    ows_server_url = settings.GEOSERVER_BASE_URL + 'ows',
    output['ows_server_url'] = ows_server_url

    # json.dumps does not like django users
    output['user'] = calculation.user.username

    # Delete _state and _user_cache item from the dict,
    # they were created automatically by Django
    del output['_user_cache']
    del output['_state']
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')


def functions(request):
    """Get a list of all the functions

       Will provide a list of plugin functions and the layers that
       the plugins will work with. Takes geoserver urls as a GET
       parameter can have a comma separated list

       e.g. http://127.0.0.1:8000/riab/api/v1/functions/?geoservers=http:...
       assumes version 1.0.0
    """

    plugin_list = get_plugins()

    if 'geoservers' in request.GET:
        # FIXME for the moment assume version 1.0.0
        geolist = request.GET['geoservers'].split(',')
        geoservers = [{'url': geoserver, 'version': '1.0.0'}
                      for geoserver in geolist]
    else:
        geoservers = get_servers(request.user)

    layers_metadata = []

    # Iterate across all available geoservers and return every layer
    # and associated keywords
    for geoserver in geoservers:
        layers_metadata.extend(
            get_layers_metadata(geoserver['url'],
                                geoserver['version']))

     # For each plugin return all layers that meet the requirements
    # an empty layer is returned where the plugin cannot run
    annotated_plugins = []
    for name, f in plugin_list.items():
        layers = compatible_layers(f, layers_metadata)

        annotated_plugins.append({
         'name': name,
         'doc': f.__doc__,
         'layers': layers,
        })

    output = {'functions': annotated_plugins}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')


def get_servers(user):
    """ Gets the list of servers for a given user
    """
    if user.is_anonymous():
        theuser = get_valid_user()
    else:
        theuser = user
    try:
        workspace = Workspace.objects.get(user=theuser)
    except Workspace.DoesNotExist:
        workspace = Workspace.objects.get(user__username='default')
    servers = workspace.servers.all()
    geoservers = [{'url': settings.GEOSERVER_BASE_URL + 'ows',
                   'name': 'Local Geoserver',
                   'version': '1.0.0', 'id':0}]
    for server in servers:
        # TODO for the moment assume version 1.0.0
        geoservers.append({'url': server.url,
                           'name': server.name,
                           'id': server.id,
                           'version': '1.0.0'})

    return geoservers


def servers(request):
    """ Get the list of all the servers registered for a given user.

        If no user is passed, it will use a default one.
    """
    geoservers = get_servers(request.user)
    output = {'servers': geoservers}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')


def layers(request):
    """ Get the list of all layers annotated with metadata

        If a parameter called 'category' is passed, it will be
        used to filter the list.
    """

    geoservers = get_servers(request.user)

    if 'category' in request.REQUEST:
        requested_category = request.REQUEST['category']
    else:
        requested_category = None
    layers_metadata = []

    # Iterate across all available geoservers and return every layer
    # and associated keywords
    for geoserver in geoservers:
        layers = get_layers_metadata(geoserver['url'],
                                     geoserver['version'])
        for layer in layers:
            out = {'name': layer[0],
                   'server_url': geoserver['url']}
            metadata = layer[1]
            name_category = out['name'].split('_')
            if 'category' in metadata.keys():
                category = metadata['category']
            elif len(name_category) > 1:
                # FIXME: This is a temporary measure until we get the keywords:
                # https://github.com/AIFDR/riab/issues/46
                # If there is no metadata then try using format category_name
                category = name_category[0]
            else:
                category = None

            if requested_category is not None:
                if requested_category == category:
                    layers_metadata.append(out)
            else:
                layers_metadata.append(out)

    output = {'objects': layers_metadata}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')
