"""Function to manage self-registering plugins

The design is based on http://effbot.org/zone/metaclass-plugins.htm

To register the plugin, the module must be imported by the Python process
using it.
"""

from django.template.loader import render_to_string
from impact.plugins.utilities import ColorMapEntry
import types
import keyword

import logging
logger = logging.getLogger('risiko')


class PluginMount(type):
    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'plugins'):
            # This branch only executes when processing the mount point itself.
            # So, since this is a new plugin type, not an implementation, this
            # class shouldn't be registered as a plugin. Instead, it sets up a
            # list where plugins can be registered later.
            cls.plugins = []
        else:
            # This must be a plugin implementation, which should be registered.
            # Simply appending it to the list is all that's needed to keep
            # track of it later.
            cls.plugins.append(cls)


class FunctionProvider:
    """Mount point for plugins which refer to actions that can be performed.

    Plugins implementing this reference should provide the following method:

    run(layers)

    ===============  =========================
    layers           A list of layers
    result           A list of layers
    ===============  =========================
    """
    __metaclass__ = PluginMount

    target_field = 'DAMAGE'
    symbol_field = 'USE_MAJOR'

    def generate_style(self, data):
        """Make a default style for all plugins
        """

        # The parameters are substituted into the sld according the the
        # Django template methodology:
        # https://docs.djangoproject.com/en/dev/ref/templates/
        #         builtins/?from=olddocs

        params = {'name': data.get_name()}

        if data.is_raster:
            colormapentries = [
                ColorMapEntry(color='#ffffff', opacity='0',
                              quantity='-9999.0'),
                ColorMapEntry(color='#38A800', opacity='0',
                              quantity='0.1'),
                ColorMapEntry(color='#38A800', quantity='0.2'),
                ColorMapEntry(color='#79C900', quantity='0.5'),
                ColorMapEntry(color='#CEED00', quantity='1'),
                ColorMapEntry(color='#FFCC00', quantity='2'),
                ColorMapEntry(color='#FF6600', quantity='3'),
                ColorMapEntry(color='#FF0000', quantity='5'),
                ColorMapEntry(color='#7A0000', quantity='9')]

            params['colormapentries'] = colormapentries
            return render_to_string('impact/styles/raster.sld', params)
        elif data.is_vector:
            params['damage_field'] = self.target_field
            return render_to_string('impact/styles/vector.sld', params)


def get_plugins(name=None):
    """Retrieve a list of plugins that match the name you pass

       Or all of them if no name is passed.
    """

    plugins_dict = dict([(pretty_function_name(p), p)
                         for p in FunctionProvider.plugins])

    if name is None:
        return plugins_dict

    if isinstance(name, basestring):
        # Add the names
        plugins_dict.update(dict([(p.__name__, p)
                                  for p in FunctionProvider.plugins]))

        msg = ('No plugin named "%s" was found. '
               'List of available plugins is: %s'
               % (name, ', '.join(plugins_dict.keys())))

        assert name in plugins_dict, msg
        return [{name: plugins_dict[name]}]
    else:
        msg = ('get_plugins expects either no parameters or a string '
               'with the name of the plugin, you passed: '
               '%s which is a %s' % (name, type(name)))
        raise Exception(msg)


def get_plugin(name):
    """Get plugin that matches given name

    This is just a wrapper around get_plugins to simplify
    """

    plugin_list = get_plugins(name)
    _, impact_function = plugin_list[0].items()[0]

    return impact_function


def pretty_function_name(func):
    """Return a human readable name for the function
    if the function has a func.plugin_name use this
    otherwise turn underscores to spaces and Caps to spaces """

    if not hasattr(func, 'plugin_name'):
        nounderscore_name = func.__name__.replace('_', ' ')
        func_name = ''
        for i, c in enumerate(nounderscore_name):
            if c.isupper() and i > 0:
                func_name += ' ' + c
            else:
                func_name += c
    else:
        func_name = func.plugin_name
    return func_name


def requirements_collect(func):
    """Collect the requirements from the plugin function doc

    The requirements need to be specified using
      :param requires <valid pythhon expression>
    The layer keywords are put into the local name space
    each requires should be on a new line
    a '/' at the end of a line will be a continuation

    returns the strings for the python exec

    Example of valid requires
    :param requires category=="impact" and subcategory.startswith("population"
    """
    requireslines = None
    if hasattr(func, '__doc__') and func.__doc__:
        docstr = func.__doc__

        require_cmd = ':param requires'

        lines = docstr.split('\n')
        requires_lines = []

        join_line = False

        for cnt, line in enumerate(lines):
            doc_line = line.strip()
            if len(doc_line) == 0:
                continue

            if join_line and not doc_line.startswith(require_cmd):
                requires_lines[-1] = requires_lines[-1][:-1] + doc_line

            elif doc_line.startswith(require_cmd):
                requires_lines.append(doc_line[len(require_cmd) + 1:])

            join_line = doc_line[-1] == '/'

    return requires_lines


def requirement_check(params, require_str, verbose=False):
    """Checks a dictionary params against the requirements defined
    in require_str. Require_str must be a valid python expression
    and evaluate to True or False"""

    # Some keyword should never go into the requirement check
    # FIXME (Ole): This is not the most robust way. If we get a
    # more general way of doing metadata we can treat caption and
    # many other things separately. See issue #148
    excluded_keywords = ['caption']

    execstr = 'def check():\n'
    for key in params.keys():
        if key == '':
            if params[''] != '':
                # This should never happen
                msg = ('Empty key found in requirements with '
                       'non-empty value: %s' % params[''])
                raise Exception(msg)
            else:
                continue

        # Check that symbol is not a Python keyword
        if key in keyword.kwlist:
            msg = ('Error in plugin requirements'
                   'Must not use Python keywords as params: %s' % (key))
            logger.error(msg)
            return False

        if key in excluded_keywords:
            continue

        if isinstance(params[key], basestring):
            execstr += '  %s = "%s" \n' % (key.strip(), params[key])
        else:
            execstr += '  %s = %s \n' % (key.strip(), params[key])

    execstr += '  return ' + require_str

    if verbose:
        print execstr
    try:
        exec(compile(execstr, '<string>', 'exec'))
        return check()
    except NameError, e:
        # This condition will happen frequently since the function
        # is evaled against many params that are not relevant and
        # hence correctly return False
        pass
    except Exception, e:
        msg = ('Requirements header could not compiled: %s. '
               'Original message: %s' % (execstr, e))
        logger.error(msg)

    return False


def requirements_met(requirements, params, verbose=False):
    """Checks the plugin can run with a given layer.

       Based on the requirements specified in the doc string.

       Returns:
           True:  if there are no requirements or they are all met.
           False: if it has requirements and none of them are met.
    """
    if len(requirements) == 0:
        # If the function has no requirements, then they are all met.
        return True

    for requires in requirements:
        if requirement_check(params, requires):
            return True

    # If none of the conditions above is met, return False.
    return False


def compatible_layers(func, layer_descriptors):
    """Fetches all the layers that match the plugin requirements.

    Input
        func: ? (FIXME(Ole): Ted, can you fill in here?
        layer_descriptor: Layer names and meta data (keywords, type, etc)

    Output:
        Array of compatible layers, can be an empty list.
    """

    layers = []
    requirements = requirements_collect(func)

    for layer_name, layer_params in layer_descriptors:
        if requirements_met(requirements, layer_params):
            layers.append(layer_name)

    return layers

#-------------------------------
# Helpers for individual plugins
#-------------------------------

def get_hazard_layers(layers):
    """Get list of layers that have category=='hazard'
    """

    return extract_layers(layers, 'category', 'hazard')


def get_hazard_layer(layers):
    """Get hazard layer from list of layers

    If there are more than one, only the first is returned.
    Use get_hazard_layers if more are expected and needed

    If no layers fit the description None is returned
    """

    L = get_hazard_layers(layers)
    if len(L) > 0:
        return L[0]
    else:
        return None


def get_exposure_layers(layers):
    """Get list of layers that have category=='exposure'
    """

    return extract_layers(layers, 'category', 'exposure')


def get_exposure_layer(layers):
    """Get exposure layer from list of layers

    If there are more than one, only the first is returned.
    Use get_hazard_layers if more are expected and needed

    If no layers fit the description None is returned
    """

    L = get_exposure_layers(layers)
    if len(L) > 0:
        return L[0]
    else:
        return None


def extract_layers(layers, keyword, value):
    """Extract layers with specified keyword/value pair
    """

    extracted_layers = []
    for layer in layers:
        if value in layer.get_keywords(keyword):
            extracted_layers.append(layer)

    return extracted_layers
