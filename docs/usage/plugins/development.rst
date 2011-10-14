==================
Plugin Development
==================

------------
Introduction
------------

Risiko contains a plugin system that allows complex impact functions to be implemented whilst (ideally) minimizing
the need to understand all the complexity of the handling the hazard and exposure layers. Features of the 
Risiko plugin system are:

* Auto registration of new plugins after restart
* Derivation of more complex plugins from simpler ones
* Auto hiding for plugins that could not be run (depending on the requirements)
* Allow for additional functionality to be added easily
* Provide uptodate documentation on plugin functionality

For details about the internal workings of the plugin subsystem please consult the developers guide in section :ref:`sec-plugin-manager`. 
There are also many examples in section showing plugins used for earthquake, tusnami and flood which can act as templates for your own plugins.  

------------------------------------
Writing a Simple Plugin: Tutorial 01
------------------------------------

This section provides a quick tutorial on how to write a very impact plugin from scratch.

Our first plugin we want to calculate a simple impact by multiplying the severity of hazard (i.e. the amount of ground shaking) by the exposure (i.e. the number of people in that area). e.g.::

    Impact =  Exposure x Hazard

Defining the impact class
+++++++++++++++++++++++++

As the first step we need to define the plugin class.::

    class SimpleImpactFunction(FunctionProvider)

Every plugin must be subclassed from FunctionProvider. This is the
method of registration for the plugin and allows the Risiko Plugin 
Manager to know what plugins are available.

Impact Parameters
+++++++++++++++++

Each plugin needs to be used in the correct context. Using a flood impact function for earthquakes may yield misleading
results at best. As such pugins may have a variety of conditions that need to be met before they can be run. Such conditions
may include:

* The type of hazard
* The type of exposure
* The form of the layer data (raster or vector)

In the future plugins may also support filtering by:
* The geographic location
* The avaliable layer meta data


These parameters required to run the plugin, and indeed all parameters specific to the plugin, 
are defined in the doc string of the class::

    class SimpleImpactFunction(FunctionProvider):
    	"""Risk plugin for simple impact calculation

    	:author Ted

    	:param requires category=="hazard" and subcategory.startswith("earthquake") and layerType=="raster"
    	:param requires category=="exposure" and subcategory.startswith("population") and layerType=="raster"
    	"""

This tells the Risiko plugin manager that this plugin requires at a minimum inputs of

* category of 'hazard', with a layer subcategory of 'earthquake' and it must be a layerType of 'Raster'
* category of 'exposure', with a layer subcategory of 'earthquake' and it must be a layerType of 'Raster'

The `require` expression can be any artibary python expression that can be evaluated.

.. note::
	1. Lines can be broken using the line continuation character '\\' at the end of a line
	2. If any one of the conditions is not met the plugin will not be visible from the impact selection box.

The calculation function
++++++++++++++++++++++++

Each plugin must then define a `run` method which is the plugin execution code::

    @staticmethod
    def run(input):
	
The parameters are passed in as a dictionary. It is up to the framework to populate the
dictionary correctly in this case with keys containing relavent data for the exposure and hazard.::

    @staticmethod
    def run(input):

        """Risk plugin for earthquake fatalities

        Input
          inputs: Specifies a dictionary containing the input paramaters for the plugin
        """

	# Get the hazard and exposure layers
        E=input['exposure']
        H=input['hazard']
        scale_constant=input('scale_constant')

        # Calculate impact
        Impact =  E * H * scale_constant

        # Return
        return Impact


At the end of the function the calculated impact is returned. This can be any object 
and it is up to the application to know what to do with the results returned

Installing the plugin
+++++++++++++++++++++

The entire plugin file is now::

    class SimpleImpactFunction(FunctionProvider):
    	"""Risk plugin for simple impact calculation

    	:author Ted

    	:param requires category=="hazard" and subcategory.startswith("earthquake") and layerType=="raster"
    	:param requires category=="exposure" and subcategory.startswith("population") and layerType=="raster"
    	"""

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

If this is saved as SimpleImpactFunction.py

Put the code in ......

Testing the plugin
++++++++++++++++++

Put the code in ......


.. warning:: One major gotcha with the plugins is that the files they are in must be imported as part of the module hierarchy consideration. This is done automatically on restart so you will need to restart Risiko to see any new plugins added.

.. note:: As the doc string is exec'ed as part of the requirements check it could be that security issues would be exposed. However it should be noted that if one can change the docstring, then any other malicious code injection would also be possible. The only objection then is that it is less noticeable in the doc string.


------------------------------------
Writing a Simple Plugin: Tutorial 02
------------------------------------


[https://github.com/AIFDR/riab/blob/develop/docs/usage/plugins/development.rst]

