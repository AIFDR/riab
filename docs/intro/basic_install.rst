========================
Quick-Start Installation
========================

This is the project: "Risiko - Risk in a Box".
The latest source code is available in https://github.com/AIFDR/riab/tree/master/impact which contains modules for risk calculations, gis functionality and plugin management.

For more information about Risk In a Box please look at
our documentation on http://risiko.readthedocs.org (for the current stable release) or http://risiko_dev.readthedocs.org (for the most recent development version)

.. FIXME: Make ole link http://riab.readthedocs.org obsolete

These are the instructions for installation of Risiko in development mode (for changing the software) and production mode (for deploying on a server).


-------------------
System Requirements
-------------------

 - A standard PC with at least 4GB of RAM.
 - The operating system is a recent version of Ubuntu Linux (http://www.ubuntu.com). Risiko has been tested on versions 10.04, 10.10 and 11.04 (32 and 64 bit).
 - The platform is using the default /etc/sources.list as it comes in a fresh Ubuntu installation. You may want to change this to a local mirror if the internet connection is slow (see e.g. https://help.ubuntu.com/community/Repositories/CommandLine) for details.
 - The user installing and running Risiko has administrator rights (using the sudo)

.. _sec-quick-start:

------------------------
Development installation
------------------------

This is for those who either want to try out the software and/or modify it. For installing Risiko as a public web server please see instructions for production installation.

To install a RISIKO development environment, start a terminal window, cd to your favorite development area and run the following::

 wget http://bit.ly/riab-install
 bash riab-install

This will create a working development installation and provide guidance on how to run the test suite, setup the server and try it.

To run the test suite, you'll need the commands::

 risiko-activate
 risiko-test

To upload the bundled demo data, you'll need to do the following::

 risiko-activate
 risiko-clean
 risiko-start
 risiko-upload risiko_demo_data

when this is finished point the browser to 127.0.0.1:8000, select layers and try the risk calculator.



Note:
If you wish to commit changes back to the repository, you must
 1. Get an account on github.com
 2. Get commit access to https://github.com/AIFDR/riab
 3. Setup and register your ssh keys with your account: https://github.com/account/ssh




===========
Limitations
===========

Risiko is a very new project. The current code development started in earnest in March 2011 and there is still much to be done.
However, we work on the philosophy that stakeholders should have access to the development and source code from the very beginning and invite comments, suggestions and contributions.


As such, Risiko currently has some major limitations, including

 * Risiko does not yet run with data loaded locally. Rather it points to a GeoServer with demo data at www.aifdr.org:8080/geoserver
 * Hazard layers must be provided as raster data
 * Exposure data must be either raster data or point vector data
 * All data must be provided in WGS84 geographic coordinates
 * Neither AIFDR nor GFDRR take any responsibility for the correctness of outputs from Risiko or decisions derived as a consequence


