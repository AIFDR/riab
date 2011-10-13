======================================
Guide to Contributing to Documentation
======================================

Introduction
------------
The documentation you are viewing is produced in Sphinx [http://sphinx.pocoo.org/] and uses ReStructured Text (ReST). To find examples of how to write in ReST for Sphinx please vist the above Sphinx web page.

Read-the-docs
-------------
The documentation for this project is automatically made by the service Read-the-Docs at [http://risiko.readthedocs.org] from the risiko git repoistory docs directory. ::

     https://github.com/AIFDR/riab/tree/develop/docs


.. note::

    if Read-the-docs does not update this can be done manually from the dashboard at [http://readthedocs.org/dashboard/risiko/ or http://readthedocs.org/dashboard/risiko_dev/]. Click on the bottom button "Build Latest Version".

Development Documentation
-------------------------

You can edit the docs straight from the git repository or after checking the repository out, making changes and pushing these changes back to github.

Changes reflected in the development branch [http://readthedocs.org/projects/risiko_dev]can be found at http://risiko_dev.readthedocs.org.

Current Stable Version 
----------------------

Documentation in the master branch [http://readthedocs.org/projects/risiko/] can be found at http://risiko.readthedocs.org.


Making the documentation
------------------------
To manually make the documentation go to the Risiko docs directory and use...

* For html::

   make html

* For latex::
  
   make latexpdf


.. note:: 
   
   In order to make the pdf documentation you will need to install the tex support. On Ubuntu you can use:

   sudo apt-get install texlive-full


To view the html documentation go to::

   [your Riskio install path]/docs/.build/html/index.html

For the pdf docs they are in::

   [your Riskio install path]/docs/.build/latex/riab.pdf

 

Documentation Structure
-----------------------

The folders follow the main documentation sections

* Intro:  Anything to do with getting started with Risiko including quick-start installation and FAQ.

* Usage: How to use Risiko, including tutorials and information on building plugins.
    - Plugins: Information about developing plugins

* Development: Information to help any serious Risiko developers, includes architecture and coding information.

* Deployment: How to deploy Risiko to various platforms.

Also:

* Images: All the images used in the documentation


