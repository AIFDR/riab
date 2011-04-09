from __future__ import division
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


from django.utils import simplejson as json
from django.http import HttpResponse
from django.conf import settings
from impact import storage, plugins, engine
from impact.models import Calculation, Workspace
from geonode.maps.utils import get_valid_user
import urlparse
import inspect
import numpy
import datetime


def calculate(request, save_output=storage.io.dummy_save):
    start = datetime.datetime.now()

    if request.method == 'GET':
        # this will not be supported in the final version,
        # it is here just for testing with default values
        AIFDR_SERVER = 'http://www.aifdr.org:8080/geoserver/ows'
        impact_function_name = 'Earthquake Fatality Function'
        bbox = '99.36,-2.199,102.237,0.00'
        hazard_server = AIFDR_SERVER
        hazard_layer = 'hazard:Earthquake_Ground_Shaking'
        exposure_server = AIFDR_SERVER
        exposure_layer = 'exposure:Population_2010'
        keywords = 'earthquake, jakarta'
    elif request.method == 'POST':
        data = request.POST
        impact_function_name = data['impact_function']
        hazard_server = data['hazard_server']
        hazard_layer = data['hazard']
        exposure_server = data['exposure_server']
        exposure_layer = data['exposure']
        bbox = data['bbox']
        keywords = data['keywords']


    # Get a valid user
    theuser = get_valid_user(request.user)

    plugin_list = plugins.get_plugins(impact_function_name)
    _, impact_function = plugin_list[0].items()[0]
    impact_function_source = inspect.getsource(impact_function)

    calculation = Calculation(user=theuser,
                              run_date=start,
                              hazard_server=hazard_server,
                              hazard_layer=hazard_layer,
                              exposure_server='exposure_server',
                              exposure_layer='exposure_layer',
                              impact_function=impact_function_name,
                              impact_function_source=impact_function_source,
                              bbox=bbox,
                              success=False,
                            )
    calculation.save()


    hazard_filename = storage.download(hazard_server, hazard_layer, bbox)
    exposure_filename = storage.download(exposure_server,
                                         exposure_layer,
                                         bbox)

    # Calculate impact using API
    HD = hazard_filename
    ED = exposure_filename
    IF = impact_function
    impact_filename = engine.calculate_impact(hazard_level=HD,
                                                   exposure_level=ED,
                                                   impact_function=IF)
    result = save_output(
                  filename=impact_filename,
                  title='output_%s' % start.isoformat(),
                  user=request.user,
                 )

    calculation.layer = result
    calculation.success = True
    calculation.save()


    output = calculation.__dict__
    # json.dumps does not like datetime objects, let's make it a json string ourselves
    output['run_date'] =  'new Date("%s")' % calculation.run_date
    # FIXME:This should not be needed in and ideal world
    output['ows_server_url'] = ows_server_url=settings.GEOSERVER_BASE_URL + 'ows',
    # json.dumps does not like django users
    output['user'] = calculation.user.username
    # Delete _state and _user_cache item from the dict, they were created automatically by Django
    del output['_user_cache']
    del output['_state']
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')


def functions(request):
    """Get a list of all the functions

       Will provide a list of plugin functions and the layers that the plugins will
       work with. Takes geoserver urls as a GET parameter can have a comma
       separated list

       e.g. http://127.0.0.1:8000/riab/api/v1/functions/?geoservers=http:...
       assumes version 1.0.0
    """


    plugin_list = plugins.get_plugins()

    if 'geoservers' in request.GET:
        #FIXME for the moment assume version 1.0.0
        geolist = request.GET['geoservers'].split(',')
        geoservers = [{'url':geoserver, 'version':'1.0.0'}
                           for geoserver in geolist]
    else:
        geoservers = get_servers(request.user)

    layers_metadata = []

    #iterate across all available geoservers and return every layer
    #and associated keywords
    for geoserver in geoservers:
        layers_metadata.extend(
            storage.get_layers_metadata(geoserver['url'],
                                          geoserver['version']))

    #for each plugin return all layers that meet the requirements
    #an empty layer is returned where the plugin cannot run
    annotated_plugins = [
        {
         'name': name,
         'doc': f.__doc__,
         'layers': plugins.compatible_layers(f, layers_metadata)}
        for name, f in plugin_list.items()]

    output = {'functions': annotated_plugins}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')


def get_servers(user):
    """ Gets the list of servers for a given user
    """
    theuser = get_valid_user(user)
    try:
        workspace = Workspace.objects.get(user=theuser)
    except Workspace.DoesNotExist:
        workspace = Workspace.objects.get(user__username='default')
    servers = workspace.servers.all()
    geoservers = [{'url': settings.GEOSERVER_BASE_URL+ 'ows',
                   'name': 'Local Geoserver',
                   'version': '1.0.0', 'id':0}]
    for server in servers:
        #TODO for the moment assume version 1.0.0
        geoservers.append({'url': server.url,
                           'name': server.name,
                           'id': server.id,
                           'version':'1.0.0'})

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
    user = get_valid_user(request.user)
    geoservers = get_servers(user)

    if 'category' in request.REQUEST:
        requested_category = request.REQUEST['category']
    else:
        requested_category = None
    layers_metadata = []
    #iterate across all available geoservers and return every layer
    #and associated keywords
    for geoserver in geoservers:
        layers = storage.get_layers_metadata(geoserver['url'],
                                        geoserver['version'])
        for layer in layers:
             out = {'name' : layer[0],
                    'server_url' : geoserver['url'],
                   }
             metadata = layer[1]
             if 'category' in metadata.keys():
                 category = metadata['category']
             else:
                 category = None

             if requested_category is not None:
                 if requested_category == category:
                     layers_metadata.append(out)
             else:
                 layers_metadata.append(out)

    output = {'objects':layers_metadata}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')
