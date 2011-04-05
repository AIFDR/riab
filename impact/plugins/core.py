from django.template.loader import render_to_string
import types

## See http://effbot.org/zone/metaclass-plugins.htm
## for a description of plugins

# FIXME(Ole): There is no information of how to register plugins e.g. by the pathname.

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

    run(hazard_layers, exposure_layers)

    ===============  =========================
    hazard_layers    A list of hazard layers
    exposure_layers  A list of exposure layers
    return_value     A numpy array
    ===============  =========================
    """
    __metaclass__ = PluginMount

    @staticmethod
    def generate_style(data):
        if data.is_raster:
            return render_to_string('webapi/styles/raster.sld')
        elif data.is_vector:
            return render_to_string('webapi/styles/vector.sld')


def get_function(name):
    """Retrieves a plugin based on it's name
    """

    plugins_dict = dict([(p.__name__, p) for p in FunctionProvider.plugins])
    return plugins_dict[name]


def pretty_function_name(func):
    """ Return a human readable name for the function
    if the function has a func.plugin_name use this
    otherwise turn underscores to spaces and Caps to spaces """

    if not hasattr(func, 'plugin_name'):
        nounderscore_name = func.__name__.replace('_', ' ')
        func_name = ""
        for i, c in enumerate(nounderscore_name):
            if c.isupper() and i > 0:
                func_name += " " + c
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

    returns the strings for the python exec

    Example of valid requires
    :param requires category=="impact" and subcategory.startswith("population"
    """
    requireslines = None
    if hasattr(func, '__doc__') and func.__doc__:
        docstr = func.__doc__

        requireCmd = ':param requires'
        requireslines = [line.strip()[len(requireCmd) + 1:]
                         for line in docstr.split('\n')
                            if line.strip().startswith(requireCmd)]

    return requireslines


def requirement_check(params, require_str, verbose=False):
    """Checks a dictionary params against the requirements defined
    in require_str. Require_str must be a valid python expression
    and evaluate to True or False"""

    execstr = "def check():\n"
    for key in params.keys():
        if type(params[key]) == type(""):  # is it a string param
            execstr += "  %s = '%s' \n" % (key.strip(), params[key])
        else:
            execstr += "  %s = %s \n" % (key.strip(), params[key])

    execstr += "  return " + require_str

    if verbose:
        print execstr
    try:
        exec(compile(execstr, "<string>", "exec"))
        return check()
    except NameError:
        pass
    except SyntaxError:
        #TODO: Something more sensible re:logging error
        print "Syntax Error", execstr
    return False


def requirements_met(func, params, verbose=False):
    """Checks to see if the plugin can run based on the requirements
       specified in the doc string"""

    requirements = requirements_collect(func)
    if requirements:
        is_met = [requirement_check(params, requires)
                  for requires in requirements]
        if True in is_met:
            return is_met.index(True)
        else:
            return False
    else:
        return None


def requirements_met_layers(func, layers_data):
    """ Returns all the layers that match the plugin requirements or
    returns [] if all requirements are not met"""

    layers = []
    requirement_satisfied = set()

    for layer_data in layers_data:
        is_met = requirements_met(func, layer_data[1])
        if type(is_met) == types.IntType:
            layers.append(layer_data[0])
            requirement_satisfied.add(is_met)

    if len(requirements_collect(func)) == len(requirement_satisfied):
        return layers
    else:
        return []
