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


from datetime import datetime
from django.utils import simplejson as json
from django.http import HttpResponse
from django.conf import settings
from impact import storage
from imact.models import Calculation
import urlparse
import inspect
import numpy

AIFDR_SERVER = 'http://www.aifdr.org:8080/geoserver/ows'


def calculate(request, save_output=storage.dummy_save):
    start = datetime.now()

    if request.method == 'GET':
        # this will not be supported in the final version,
        # it is here just for testing with default values
        impact_function = 'EarthquakeFatalityFunction'
        bbox = '99.36,-2.199,102.237,0.00'
        hazard_server = AIFDR_SERVER
        hazard_layer = 'hazard:Earthquake_Ground_Shaking'
        exposure_server = AIFDR_SERVER
        exposure_layer = 'exposure:Population_2010'
        keywords = 'earthquake, jakarta'
    elif request.method == 'POST':
        data = request.POST
        impact_function = data['impact_function']
        hazard_server = data['hazard_server']
        hazard_layer = data['hazard']
        exposure_server = data['exposure_server']
        exposure_layer = data['exposure']
        bbox = data['bbox']
        keywords = data['keywords']

    now = datetime.datetime.now()

    # Get a valid user
    theuser = get_valid_user(user)

    impact_function_name = metadata['impact_function']
    impact_function = get_function(impact_function_name)
    impact_function_source = inspect.getsource(impact_function)

    calculation = Calculation(user=theuser,
                              run_date=now,
                              hazard_server=metadata['hazard_server'],
                              hazard_layer=metadata['hazard_layer'],
                              exposure_server=metadata['exposure_server'],
                              exposure_layer=metadata['exposure_layer'],
                              impact_function=impact_function_name,
                              impact_function_source=impact_function_source,
                              bbox=metadata['bbox'],
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
    IF = riab_server.get_function(impact_function)
    impact_filename = riab_server.calculate_impact(hazard_level=HD,
                                                   exposure_level=ED,
                                                   impact_function=IF)
    result = save_output(
                  filename=impact_filename,
                  title='output_%s' % start.isoformat(),
                  user=request.user,
                  metadata=dict(
                             keywords=keywords,
                             hazard_server=hazard_server,
                             hazard_layer=hazard_layer,
                             exposure_server=exposure_server,
                             exposure_layer=exposure_layer,
                             impact_function=impact_function,
                             bbox=bbox,
                             abstract=('Calculated by Risk In a Box'
                                      'using %s and %s with %s' %
                                       (hazard_layer,
                                        exposure_layer,
                                        impact_function))))

    if isinstance(result, basestring):
        # If it's a string, the we got the url
        output = {'success': True, 'layer_url': result}
    elif  isinstance(result, (list, tuple)):
        output = {'success': False, 'errors': result}
    else:
        output = {'success': False,
                  'errors': ["""The function did not return a url
                             nor a list of error. Call me if this happens"""]}

    calculation.layer = layer
    calculation.success = True
    calculation.save()


    output = dict(impact_function=impact_function,
                  bbox=bbox,
                  hazard=hazard_layer,
                  exposure=exposure_layer,
                  result=output,
                  ows_server_url=settings.GEOSERVER_BASE_URL + 'ows',
                  keywords=keywords,
                  run_date='new Date("%s")' % calculation.run_date,
                  run_duration=calculation.duration,
                  )
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')

## Will provide a list of plugin functions and the layers that the plugins will
## work with. Takes geoserver urls as a GET parameter can have a comma
## separated list
##
## e.g. http://127.0.0.1:8000/riab/api/v1/functions/?geoservers=http:...
## assumes version 1.0.0


def functions(request):
    """Get a list of all the functions
    """
    plugins = riab_server.FunctionProvider.plugins
    plugin_tools = riab_server.function.plugins

    if 'geoservers' in request.GET:
        #TODO for the moment assume version 1.0.0
        geolist = request.GET['geoservers'].split(',')
        geoservers = [{'url':geoserver, 'version':'1.0.0'}
                           for geoserver in geolist]
    else:
        # TODO: need to fetch the list of servers from GeoNode
        # hardcoded for the moment
        geoservers = [{'url': 'http://www.aifdr.org:8080/geoserver/ows',
                       'version': '1.0.0'}]

    layers_metadata = []

    #iterate across all available geoservers and return every layer
    #and associated keywords
    for geoserver in geoservers:
        layers_metadata.extend(
            utilities.get_layers_metadata(geoserver['url'],
                                          geoserver['version']))

    #for each plugin return all layers that meet the requirements
    #an empty layer is returned where the plugin cannot run
    requirements_met_plugins = [
        {
         'id': f.__name__,
         'name': plugin_tools.pretty_function_name(f),
         'doc': f.__doc__,
         'layers': plugin_tools.requirements_met_layers(f, layers_metadata)}
        for f in plugins]

    output = {'functions': requirements_met_plugins}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')


def get_servers(user):
    """ Gets the list of servers for a given user
    """
    try:
        workspace = Workspace.objects.get(user=user)
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
    user = valid_user(request.user)
    geoservers = get_servers(user)
    output = {'servers': geoservers}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')

def layers(request):
    """ Get the list of all layers annotated with metadata

        If a parameter called 'category' is passed, it will be
        used to filter the list. For example:

        >>> category = request.POST['category']
        >>> category
        'hazard'
        >>> layers = Layer.objects.filter(category='hazard')
        >>> return json.dumps(layers)
    """
    user = good_user(request.user)
    geoservers = get_servers(user)

    if 'category' in request.REQUEST:
        requested_category = request.REQUEST['category']
    else:
        requested_category = None
    layers_metadata = []
    #iterate across all available geoservers and return every layer
    #and associated keywords
    for geoserver in geoservers:
        layers = get_layers_metadata(geoserver['url'],
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

