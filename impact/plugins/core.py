from django.template.loader import render_to_string
import types

## See http://effbot.org/zone/metaclass-plugins.htm
## for a description of plugins

# To register the plugin, the module must be imported by the Python process
# using it.
# FIXME (Ole): I think we should pass the module name to get_function to
#              keep things together


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
    """
    Mount point for plugins which refer to actions that can be performed.

    Plugins implementing this reference should provide the following method:

    run(layers)

    ===============  =========================
    layers           A list of layers
    result           A list of layers
    ===============  =========================
    """
    __metaclass__ = PluginMount

    @staticmethod
    def generate_style(data):
        params = {
                   'name': data.get_name(),
        }
        if data.is_raster:
            return render_to_string('impact/styles/raster.sld', params)
        elif data.is_vector:
            #FIXME: How do we get the target_value from here?
            params['damage'] = 'Percent_da'
            params['stroke'] = False
            return render_to_string('impact/styles/vector.sld', params)


def get_plugins(name=None):
    """Retrieves a list of plugins that match the name you pass

       Or all of them if no name is passed.
    """

    plugins_dict = dict([(pretty_function_name(p), p)
                         for p in FunctionProvider.plugins])

    if name is None:
        return plugins_dict

    if isinstance(name, basestring):
        print
        print 'name', name

        for p in FunctionProvider.plugins:
            print p

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


def pretty_function_name(func):
    """ Return a human readable name for the function
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
    """ Collect the requirements from the plugin function doc

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

        if type(params[key]) == type(''):  # is it a string param
            execstr += '  %s = "%s" \n' % (key.strip(), params[key])
        else:
            execstr += '  %s = %s \n' % (key.strip(), params[key])

    execstr += '  return ' + require_str

    if verbose:
        print execstr
    try:
        exec(compile(execstr, '<string>', 'exec'))
        return check()
    except NameError:
        pass
    except SyntaxError:
        # TODO(Ted and Ole): This exceptions should be handle by the callee
        #                    as we don't want errors in plugins to
        #                    crash the system.
        msg = 'Syntax error in plugin requirements header: %s' % execstr
        raise SyntaxError(msg)
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


def compatible_layers(func, layers_data):
    """Fetches all the layers that match the plugin requirements.

       Returns:

           Array of compatible layers, can be an empty list.
    """
    layers = []
    requirements = requirements_collect(func)

    for layer_name, layer_params in layers_data:
        if requirements_met(requirements, layer_params):
            layers.append(layer_name)

    return layers
