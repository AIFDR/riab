Frequently Asked Questions
==========================



How do I rename a shape file and all the helper files?
::
  Use the rename command. rename [ -v ] [ -n ] [ -f ] perlexpr [ files ].
  For example
    rename -v 's/^building/OSM_building_polygons_20110905/' building.*


My Risiko production server is live but no map shows?
::
  Try to login and restart tomcat: sudo /etc/init.d/tomcat6 restart

How do I get Open Street Map building data?
::
  For Indonesian, you can download latest collections at http://data.kompetisiosm.org
