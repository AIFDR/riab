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

import sys
import inspect
import datetime

from django.utils import simplejson as json
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from impact.storage.io import dummy_save, download
from impact.storage.io import get_metadata, get_layer_descriptors
from impact.storage.io import bboxlist2string
from impact.storage.io import save_to_geonode
from impact.storage.utilities import titelize
from impact.plugins.core import get_plugin, get_plugins, compatible_layers
from impact.engine.core import calculate_impact
from impact.engine.core import get_common_resolution, get_bounding_boxes
from impact.models import Calculation, Workspace

from geonode.maps.utils import get_valid_user

from urlparse import urljoin

import logging
logger = logging.getLogger('risiko')


def exception_format(e):
    """Convert an exception object into a string,
    complete with stack trace info, suitable for display.
    """
    import traceback
    info = ''.join(traceback.format_tb(sys.exc_info()[2]))
    return str(e) + '\n\n' + info


@csrf_exempt
def calculate(request, save_output=save_to_geonode):
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
        requested_bbox = data['bbox']
        keywords = data['keywords']

    if request.user.is_anonymous():
        theuser = get_valid_user()
    else:
        theuser = request.user

    # Create entry in database
    calculation = Calculation(user=theuser,
                              run_date=start,
                              hazard_server=hazard_server,
                              hazard_layer=hazard_layer,
                              exposure_server=exposure_server,
                              exposure_layer=exposure_layer,
                              impact_function=impact_function_name,
                              success=False)

    # Wrap main computation loop in try except to catch and present
    # messages and stack traces in the application
    try:
        # Get metadata
        haz_metadata = get_metadata(hazard_server, hazard_layer)
        exp_metadata = get_metadata(exposure_server, exposure_layer)

        # Determine common resolution in case of raster layers
        raster_resolution = get_common_resolution(haz_metadata, exp_metadata)

        # Get reconciled bounding boxes
        haz_bbox, exp_bbox, imp_bbox = get_bounding_boxes(haz_metadata,
                                                          exp_metadata,
                                                          requested_bbox)

        # Record layers to download
        download_layers = [(hazard_server, hazard_layer, haz_bbox),
                           (exposure_server, exposure_layer, exp_bbox)]

        # Add linked layers if any FIXME: STILL TODO!

        # Get selected impact function
        impact_function = get_plugin(impact_function_name)
        impact_function_source = inspect.getsource(impact_function)

        # Record information calculation object and save it
        calculation.impact_function_source = impact_function_source
        calculation.bbox = bboxlist2string(imp_bbox)
        calculation.save()

        # Start computation
        msg = 'Performing requested calculation'
        logger.info(msg)

        # Download selected layer objects
        layers = []
        for server, layer_name, bbox in download_layers:
            msg = ('- Downloading layer %s from %s'
                   % (layer_name, server))
            logger.info(msg)
            L = download(server, layer_name, bbox, raster_resolution)
            layers.append(L)

        # Calculate result using specified impact function
        msg = ('- Calculating impact using %s' % impact_function)
        logger.info(msg)
        impact_filename = calculate_impact(layers=layers,
                                           impact_fcn=impact_function)

        # Upload result to internal GeoServer
        msg = ('- Uploading impact layer %s' % impact_filename)
        logger.info(msg)
        result = save_output(impact_filename,
                             title='output_%s' % start.isoformat(),
                             user=theuser)
    except Exception, e:
        # FIXME: Reimplement error saving for calculation.
        # FIXME (Ole): Why should we reimplement?
        # This is dangerous. Try to raise an exception
        # e.g. in get_metadata_from_layer. Things will silently fail.
        # See issue #170

        logger.error(e)
        errors = e.__str__()
        trace = exception_format(e)
        calculation.errors = errors
        calculation.stacktrace = trace
        calculation.save()
        jsondata = json.dumps({'errors': errors, 'stacktrace': trace})
        return HttpResponse(jsondata, mimetype='application/json')

    msg = ('- Result available at %s.' % result.get_absolute_url())
    logger.info(msg)

    calculation.layer = urljoin(settings.SITEURL, result.get_absolute_url())
    calculation.success = True
    calculation.save()

    output = calculation.__dict__

    # json.dumps does not like datetime objects,
    # let's make it a json string ourselves
    output['run_date'] = 'new Date("%s")' % calculation.run_date

    # FIXME: This should not be needed in an ideal world
    ows_server_url = settings.GEOSERVER_BASE_URL + 'ows',
    output['ows_server_url'] = ows_server_url

    # json.dumps does not like django users
    output['user'] = calculation.user.username
    downloads = result.download_links()
    keys = [x[0] for x in downloads]
    values = [x[2] for x in downloads]
    download_dict = dict(zip(keys, values))
    if 'excel' in keys:
        output['excel'] = download_dict['excel']

    # Keywords do not like caption being there.
    # FIXME: Do proper parsing, don't assume caption is the only keyword.
    if 'caption' in result.keywords:
        caption = result.keywords.split('caption:')[1]
        # FIXME (Ole): Return underscores to spaces that was put in place
        # to store it in the first place. See issue #148
        output['caption'] = caption.replace('_', ' ')
    else:
        output['caption'] = 'Calculation finished ' \
                            'in %s' % calculation.run_duration

    # Delete _state and _user_cache item from the dict,
    # they were created automatically by Django
    del output['_user_cache']
    del output['_state']

    # If success == True and errors = '' ...
    # ... let's make errors=None for backwards compat
    if output['success'] and len(output['errors']) == 0:
        output['errors'] = None

    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')


def debug(request):
    """Show a list of all the functions"""
    plugin_list = get_plugins()

    plugins_info = []
    for name, f in plugin_list.items():
        if not 'doc' in request.GET:
            plugins_info.append({
             'name': name,
             'location': f.__module__,
            })
        else:
            plugins_info.append({
             'name': name,
             'location': f.__module__,
             'doc': f.__doc__,
            })

    output = {'plugins': plugins_info}
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

    # Iterate across all available geoservers and return all
    # layer descriptors for use with the plugin subsystem
    layer_descriptors = []
    for geoserver in geoservers:
        layer_descriptors.extend(
            get_layer_descriptors(geoserver['url']))

    # For each plugin return all layers that meet the requirements
    # an empty layer is returned where the plugin cannot run
    annotated_plugins = []
    for name, f in plugin_list.items():
        layers = compatible_layers(f, layer_descriptors)

        annotated_plugins.append({'name': name,
                                  'doc': f.__doc__,
                                  'layers': layers})

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

    # FIXME (Ole): Why does the word 'category' have a special meaning?
    #              Someone, please revisit this code!

    geoservers = get_servers(request.user)

    if 'category' in request.REQUEST:
        requested_category = request.REQUEST['category']
    else:
        requested_category = None

    # Iterate across all available geoservers and all layer descriptors
    layer_descriptors = []
    for geoserver in geoservers:
        ld = get_layer_descriptors(geoserver['url'])
        for layer in ld:
            out = {'name': layer[0],
                   'title': titelize(layer[1]['title']),
                   'server_url': geoserver['url']}
            metadata = layer[1]
            name_category = out['name'].split('_')
            if 'category' in metadata.keys():
                category = metadata['category']
            elif len(name_category) > 1:
                # FIXME: This is a temporary measure until we get the keywords:
                # https://github.com/AIFDR/riab/issues/46
                # If there is no metadata then try using format category_name
                # FIXME (Ole): This section should definitely be cleaned up
                # FIXME (Ole): CLEAN IT - NOW!!!
                category = name_category[0]
            else:
                category = None

            if requested_category is not None:
                if requested_category == category:
                    layer_descriptors.append(out)
            else:
                layer_descriptors.append(out)

    output = {'objects': layer_descriptors}
    jsondata = json.dumps(output)
    return HttpResponse(jsondata, mimetype='application/json')
