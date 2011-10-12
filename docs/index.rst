.. _index:

.. image:: http://riskinabox.org/media/riab-logo.png
	:scale: 50 %
	:align: center

======================
Risiko's documentation
======================

.. rubric:: Risiko is a web based tool that models impacts of different hazard events on population or infrastructure. It is part of a set of Open Source Software tools called Risk in a Box, and we encourage you to build new applications using its components and the resources it provides. The project home page can be found at http://riskinabox.org/


.. figure:: images/screenshot.png
	:scale: 76 %
        
        Risiko Screenshot showing earthquake hazard in Indonesia


=============================
Introduction and Installation
=============================

.. toctree::
   :maxdepth: 3
   :numbered:

   intro/basic_install
   intro/faq
   
===========
Usage Guide
===========

.. toctree::
   :maxdepth: 3
   :numbered:

   usage/overview
   usage/risiko_calculator
   usage/plugins/development
   
   
===============
Developer Guide
===============

.. toctree::
   :maxdepth: 3
   :numbered:

   development/overview
   development/architecture
   development/pluginmanager
   development/documentation
   development/contributing
   development/release-process
   development/git
   development/dev_help


===========================
Production Deployment Guide
===========================

.. toctree::
   :maxdepth: 3
   :numbered:

   deployment/production_install
   


The code
========

    * **Core Module:**
      :doc:`Calculation Engine  <code/core/engine>` |
      :doc:`Working with raster data <code/core/raster>` |
      :doc:`Working with vector data <code/core/vector>` |
      :doc:`Interpolation <code/core/interpolation>` |
      :doc:`Projections <code/core/projections>`

    * **HTTP REST API (RiaB Server):**
      :doc:`API Description <code/http/api>` |
      :doc:`GeoNode/GeoServer upload/download <code/http/geonode>` |
      :doc:`Debugging and extending tips and tricks <code/http/tips>`

    * **Impact functions plugins:**
      :doc:`Plugin system <code/function/plugins>` |
      :doc:`Creating and registering new functions <code/function/extending>`

    * **Exceptions:**
      :doc:`Overview <code/exceptions>`

    * **Testing:**
      :doc:`Overview <code/testing>`



