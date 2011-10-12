==============
Plugin Manager
==============

The plugin manager keeps track of all the plugins and searching, requirements checking and retrieval functions. Communications with the plugin are achieved through the application passing in a dictionary and recieving back an object in return. The application should know what to do with the object on return.

.. figure:: https://docs.google.com/drawings/pub?id=12xmm97658xWAY7bjQ4b6MicKd_l3IpP5ZIKT96RF1XM&w=640&h=480

    :scale: 25 %
    
    Plugin connectivity. Plugins can derive from base plugins (Plugin 1 -> Plugin 1a). Objects or dictionaries are passed down and results of the plugin are passed back to the application 

    
.. raw:: html

    <div class="prezi-player"><style type="text/css" media="screen">.prezi-player { width: 550px; } .prezi-player-links { text-align: center; }</style><object id="prezi_kbelff3fw__7" name="prezi_kbelff3fw__7" classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" width="550" height="400"><param name="movie" value="http://prezi.com/bin/preziloader.swf"/><param name="allowfullscreen" value="true"/><param name="allowscriptaccess" value="always"/><param name="bgcolor" value="#ffffff"/><param name="flashvars" value="prezi_id=kbelff3fw__7&amp;lock_to_path=0&amp;color=ffffff&amp;autoplay=no&amp;autohide_ctrls=0"/><embed id="preziEmbed_kbelff3fw__7" name="preziEmbed_kbelff3fw__7" src="http://prezi.com/bin/preziloader.swf" type="application/x-shockwave-flash" allowfullscreen="true" allowscriptaccess="always" width="550" height="400" bgcolor="#ffffff" flashvars="prezi_id=kbelff3fw__7&amp;lock_to_path=0&amp;color=ffffff&amp;autoplay=no&amp;autohide_ctrls=0"></embed></object><div class="prezi-player-links"><p><a title="Python Plugin" href="http://prezi.com/kbelff3fw__7/pylightplug/">PyLightPlug</a> on <a href="http://prezi.com">Prezi</a></p></div></div>

When building your plugin manager the following functions are exposed by PyLightPlug::
        
    def get_function(name):
        """Retrieves a plugin based on it's name
        """

    def pretty_function_name(func):
        """ Return a human readable name for the function
        if the function has a func.plugin_name use this
        otherwise turn underscores to spaces and Caps to spaces """
        
    def requirements_collect(func):
        """ Collect the requirements from the plugin function doc
        The requirements need to be specified using
          :param requires <valid pythhon expression>
        The layer keywords are put into the local name space
        each requires should be on a new line    
        returns the strings for the python exec

        Example of valid requires
        :param requires category=="impact" and subcategory.startswith("population")
        """
    
    def requirement_check(params, require_str, verbose=False):
        """Checks a dictionary params against the requirements defined
        in require_str. Require_str must be a valid python expression
        and evaluate to True or False"""
    
    def requirements_met(func, params, verbose=False):
        """Checks to see if the plugin can run based on the requirements
           specified in the doc string"""
    

The sequence of calls for the pyPluginManager is to use the requirements met function to determine
which plugins can run by passing a dictionary  `params` to the discovered plugins. Once the plugins
the can run have been discovered `get_function` can be called to obtain a handle to the plugin. The 
plugin can then be executed using the following type of call::
  
    my_plugin = get_function('EarthquakeFatalityFunction')
    input_params = dict(category = 'hazard', subcategory='....')
    if requirement_met(my_plugin,params = input_params):
        my_plugin.run(input_params)
    
    
-------------------------------
Getting a list of valid plugins
-------------------------------

To get a list of plugins that can execute for a given context (i.e. from a menu or selection box) all available plugins must be checked to see if the requirements are met::

    input_params = dict(category = 'hazard', subcategory='....')
    plugin_list=plugins_requirements_met(input_params)
    plugin_names = [pretty_function_name(func) for func in plugin_list]
