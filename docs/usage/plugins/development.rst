==================
Plugin Development
==================

------------
Introduction
------------

There are many ways of developing plugin systems, and every project has different requirements. Some requirements that are common, particularly for scientific apps, include: 

* Auto registration of new plugins and the automatic update during development
* Derivation of more complex plugins from simpler ones
* Specifying parameters that can be passed to the plugin
* Have the plugin manager determine which plugins can be used at any time
* Allow for additional functionality to be added easily
* Provide good documentation on functionality

-----------------------
Writing a Simple Plugin
-----------------------

Our first plugin we want to calculate a simple impact by multiplying the severity of hazard (i.e. the amount of ground shaking) by the exposure (i.e. the number of people in that area). e.g.::

    Impact =  Exposure x Hazard

As the first step we need to define the plugin class.::

    class EarthquakeFatalityFunction(FunctionProvider):
          pass

Every plugin must be subclassed from FunctionProvider. This is the 
method of registration for the plugin and allows the Plugin Manager to know what plugins are available.

The parameters required to run the plugin, and indeed all parameters specific to the plugin, are defined in the doc string of the class::

    class EarthquakeFatalityFunction(FunctionProvider):
    	"""Risk plugin for earthquake damage

    	:author Ted

    	:param requires category=="hazard" and subcategory.startswith("earthquake") and layerType=="raster"
    	:param requires category=="exposure" and subcategory.startswith("population") and layerType=="raster"
    	"""

This tells the PyLightPlug manager that this plugin requires inputs of

* category of 'hazard', with a subcategory of 'earthquake' and it must be a layerType of 'Raster'
* category of 'exposure', with a subcategory of 'earthquake' and it must be a layerType of 'Raster'

.. note:: Lines can be broken using the line continuation character '\\' at the end of a line

Each plugin must define a `run` method which is the plugin execution code::

    @staticmethod
    def run(input):
        """Risk plugin for earthquake fatalities

        Input
          inputs: Specifies a dictionary containing the input paramaters for the plugin
        """
        E=input['exposure']
        H=input['hazard']
        scale_constant=input('scale_constant')
        
        # Calculate impact
        Impact =  E * H * scale_constant

        # Return
        return Impact


The parameters are passed in as a dictionary. It is up to the framework to populate the dictionary correctly in this case with keys containing relavent data for the exposure and hazard.

At the end of the function the calculated impact is returned. This can be any object and it is up to the application to know what to do with the results returned

.. warning:: One major gotcha with the plugins is that the files they are in must be imported as part of the module hierarchy consideration. This can be done in the __init__ file. Support may be provided in the future to import all python files under a given directory (i.e. force_import_plugins(dir))

.. note:: As the doc string is exec'ed as part of the requirements check it could be that security issues would be exposed. However it should be noted that if one can change the docstring, then any other malicious code injection would also be possible. The only objection then is that it is less noticeable in the doc string.

.. [#metaclass_link] This link has a good decription of a metaclass plugin implemtation http://effbot.org/zone/metaclass-plugins.htm
 
