============
Introduction
============

.. topic:: PyLightPlug

  A light weight python plugin system for scientific applications 

--------
Rational
--------

Many python projects require plug-in functionality. This is particularly true of scientific applications where it is expected that the user will want to extend the out-of-the box abilities of an application for instance adding new graph types or customized functions.

There are a number of different plugin systems avaliable, however many suffer from being either inflexible or too heavy weight. There are however some good plug-in patterns avaliable and developers frequently 'roll-there-own'
to suit the application requirements. It is the aim of this module to provide the basis for a flexible plugin-system that can be used for a wide variety of different applications and allow the developer to focus on the app not on the plugin system, and the user to be able to simply build plugins.

PyLightPlug uses meta classes and doc string introspection that is tailored for scientific applications. It aims to provides the following benefits:

#. Documentation: A structured doc string is used as part of the specification for the plugin. The format follows the Sphinx standard and hence provides well documented user information about the plugin. The same information is also is used to determine if the plugin can run (requirements filtering) as well as other display related attributes.
#. Requirements Filtering: Requirements are filtered based on one or more evaluated commands embedded in the doc string using a sphinx like format. These are used to determine if a plugin can run based on meta-data provided as dictionaries by the plugin manager.
#. Data Handing: A method of handling collections of scientific data based on flickr style tags.
#. Post Processing Decoration: A flexible decoration post processor to customize the styling of any output.
#. Debugging: Plugins can be easily debugged and tested via a command line interface. This ensures that plugin errors can be handled appropriately and also that changes to plugins are dynamically refreshed without requiring an application restart.
#. Rest Interface: An infrastructure that includes the batteries for using the plugin with web infrastructure.
#. Security:  The prevention of malicious plugin code by restricting the execution environment
#. Sharing: The ability to easily share developed plugins.
#. Light-Weight: The library is designed to be a compact and well documented

-------
History
-------

This module was developed as part of the Risiko project. Risiko is a Python/Django application that will model impacts of different hazard events on population or infrastructure using distributed spatial hazard and exposure data hosted using spatial data management frameworks from OpenGeo. This will allow local authorities to undertake generalimpact modelling to better prepare their local communities for the impact of natural disasters. (www.riskinabox.org)
