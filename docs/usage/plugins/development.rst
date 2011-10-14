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
There are also many examples in this section showing plugins used for earthquake, tusnami and flood which can act as templates for your own plugins.  

-------------------------------------------
Writing a Simple Raster Plugin: Tutorial 01
-------------------------------------------

This section provides a beginners tutorial on writing a simple earthquke impact plugin from scratch.

For this plugin we want to calculate a simple impact by using the following function of 
the severity of hazard (i.e. the amount of ground shaking - H) by the exposure 
(i.e. the number of people in that area - P). e.g.::

    Impact  = 10 ** (a * H - b) * P
    
    where 
          H: Raster layer of MMI ground shaking
          P: Raster layer of population data on the same grid as H
          a,b: Parameters that were tuned from real world data
 

Defining the impact class
+++++++++++++++++++++++++

As the first step we need to define the plugin class.::

    class SimpleImpactEarthquakeFunction(FunctionProvider)

Every plugin must be subclassed from FunctionProvider. This is the
method of registration for the plugin and allows the Risiko Plugin 
Manager to know what plugins are available.

Impact Parameters
+++++++++++++++++

Each plugin needs to be used in the correct context. Using a flood impact function for earthquakes will likely yield misleading
results at best! As such pugins may have a variety of conditions that need to be met before they can be run. Such conditions
may include:

* The type of hazard
* The type of exposure
* The form of the layer data (raster or vector)

In the future plugins may also support filtering by:
* The geographic location
* The avaliable layer meta data

Risiko will try to show users only those plugins that can be validly run.

These parameters required to run the plugin, and indeed all parameters specific to the plugin, 
are defined in the doc string of the class::

     class SimpleImpactEarthquakeFunction(FunctionProvider):
        """Simple plugin for earthquake damage

        :author Allen
        :rating 1
        :param requires category=='hazard' and \
                subcategory.startswith('earthquake') and \
                layer_type=='raster'
        :param requires category=='exposure' and \
                subcategory.startswith('population') and \
                layer_type=='raster'
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
    def run(layers,
            a=0.97429, b=11.037):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of MMI ground shaking
              P: Raster layer of population data on the same grid as H
        """

        # Identify input layers
        intensity = layers[0]
        population = layers[1]

        # Extract data
        H = intensity.get_data(nan=0)
        P = population.get_data(nan=0)

        # Calculate impact
        F = 10 ** (a * H - b) * P

        # Create new layer and return
        R = Raster(F,
                   projection=population.get_projection(),
                   geotransform=population.get_geotransform(),
                   name='Estimated fatalities')
        return R



At the end of the function the calculated impact layer R is returned. This return layer 
in our example is a Raster layer the correct projection for this layer is ensured by passing
in the input layer projections.


Installing the plugin
+++++++++++++++++++++

The entire plugin file is now::

    from impact.plugins.core import FunctionProvider
    from impact.storage.raster import Raster

    class SimpleImpactEarthquakeFunction(FunctionProvider):
        """Simple plugin for earthquake damage

        :author Allen
        :rating 1
        :param requires category=='hazard' and \
                subcategory.startswith('earthquake') and \
                layer_type=='raster'
        :param requires category=='exposure' and \
                subcategory.startswith('population') and \
                layer_type=='raster'
        """

    @staticmethod
    def run(layers,
            a=0.97429, b=11.037):
        """Risk plugin for earthquake fatalities

        Input
          layers: List of layers expected to contain
              H: Raster layer of MMI ground shaking
              P: Raster layer of population data on the same grid as H
        """

        # Identify input layers
        intensity = layers[0]
        population = layers[1]

        # Extract data
        H = intensity.get_data(nan=0)
        P = population.get_data(nan=0)

        # Calculate impact
        F = 10 ** (a * H - b) * P

        # Create new layer and return
        R = Raster(F,
                   projection=population.get_projection(),
                   geotransform=population.get_geotransform(),
                   name='Estimated fatalities')
        return R

If this is saved as SimpleImpactEarthquakeFunction.py

Put the code in the plugins/earthquake directory. Restart Risiko using::

	risiko-stop
	risiko-start

Testing the plugin
++++++++++++++++++


If you now go to your local Riskio install (by default 127.0.0.1:8000) you can select the following from the demo data:

.. note:: If you don't see any demo data please follow the quick start instructions 


.. warning:: One major gotcha with the plugins is that the files they are in must be imported as part of the module hierarchy consideration. This is done automatically on restart so you will need to restart Risiko to see any new plugins added.


-------------------------------------------
Writing a Simple Vector Plugin: Tutorial 02
-------------------------------------------


[https://github.com/AIFDR/riab/blob/develop/docs/usage/plugins/development.rst]

