============
DEVELOPMENT
============

To install a RISIKO development environment on a Ubuntu Linux system, cd to your favorite development area and run the following::

 wget https://github.com/AIFDR/riab/raw/master/scripts/risiko-install --no-check-certificate
 bash risiko-install

This will create a working development installation and provide guidance on how to run the test suite, setup the server and try it.

Note:
If you wish to commit changes back to the repository, you must
 1. Get an account on github.com
 2. Get commit access to https://github.com/AIFDR/riab
 3. Setup and register your ssh keys with your account: https://github.com/account/ssh

===========
PRODUCTION
===========

It is assumed that a development system is already running ((installed as per instructions above) and that the production system is a separate Ubuntu server.

To deploy RISIKO in production mode from your development system to the remote server::

 risiko-activate
 cd $RIAB_HOME/riab/extras
 fab risiko -H username@remote.server


