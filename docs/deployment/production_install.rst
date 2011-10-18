Deployment
==========

Production installation 
-----------------------

(Obsolete!)

This is for installing Risiko as a public web server.

It is assumed that a development system is already running (installed as per instructions above) and that the production system is a separate server that can be accessed via ssh (ssh username@remote.server).

To deploy RISIKO in production mode from your development system to the remote server run the following::

 risiko-activate
 cd $RIAB_HOME/riab/extras
 fab risiko -H username@remote.server

If something goes wrong, you can check the logs with the command::

 fab log -H username@remote.server

You can update an existing production system to the latest revision with the command::

  fab pull -H username@remote.server


The production deployment procedure is scripted in the file fabfile.py and the fabric framework is documented at http://docs.fabfile.org

Live USB drive
--------------

Install RISIKO on a live USB drive.

# This text should probably go into a different file

1. Create Ubuntu live USB drive:
  - http://www.pendrivelinux.com/universal-usb-installer-easy-as-1-2-3 or http://www.linuxliveusb.com/
  - https://wiki.ubuntu.com/LiveUsbPendrivePersistent (paragraph starting with "To make the persistence larger")

2. Install Risiko normally as detailed in INSTALL.rst

