======================
RISIKO - RISK IN A BOX
======================

This is the project: "Risiko - Risk in a Box".
It consists of the following modules:

- https://github.com/AIFDR/riab/tree/master/risiko: The web application
- https://github.com/AIFDR/riab/tree/master/impact: Module for risk calculations, gis functionality and plugin management

For more information about Risk In a Box please look at
our documentation on http://riab.readthedocs.org


============
INSTALLATION
============

These are the instructions for installation of Risiko in development mode (for changing the software) and production mode (for deploying on a server).


-------------------
System Requirements
-------------------

 - A standard PC with at least 4GB of RAM.
 - The operating system is a recent version of Ubuntu Linux. Risiko has been tested on versions 10.04 and 10.10 (32 and 64 bit).
 - The platform is using the default /etc/sources.list as it comes in a fresh Ubuntu installation. You may want to change this to a local mirror if the internet connection is slow (see e.g. https://help.ubuntu.com/community/Repositories/CommandLine) for details.


-----------
Development
-----------

To install a RISIKO development environment, cd to your favorite development area and run the following::

 wget https://github.com/AIFDR/riab/raw/master/scripts/risiko-install --no-check-certificate
 bash risiko-install

This will create a working development installation and provide guidance on how to run the test suite, setup the server and try it.

Note:
If you wish to commit changes back to the repository, you must
 1. Get an account on github.com
 2. Get commit access to https://github.com/AIFDR/riab
 3. Setup and register your ssh keys with your account: https://github.com/account/ssh

----------
Production
----------

It is assumed that a development system is already running ((installed as per instructions above) and that the production system is a separate server that can be accessed via ssh (ssh username@remote.server).

To deploy RISIKO in production mode from your development system to the remote server run the following::

 risiko-activate
 cd $RIAB_HOME/riab/extras
 fab risiko -H username@remote.server

If something goes wrong, you can check the logs with the command::

 fab log -H username@remote.server

You can update an existing production system to the latest revision with the command::

  fab pull -H username@remote.server


The production deployment procedure is scripted in the file fabfile.py and the fabric framework is documented at http://docs.fabfile.org
