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
  For Indonesia, you can download latest collections at http://data.kompetisiosm.org

How do I take screen capture e.g. for use in a presentation?
::
  On Ubuntu, get the packages gtk-recordmydesktop and mencoder
  Record using recordmydesktop (start and stop icon in the top bar)
  Convert to other formats using mencoder, e.g.
  mencoder -idx yogya_analysis-6.ogv -ovc lavc -oac lavc -lavcopts vcodec=mpeg4:vpass=1 -of lavf -o yogya_analysis.avi
  or
  mencoder -idx yogya_analysis-6.ogv -ovc lavc -oac lavc -lavcopts vcodec=wmv2 -of lavf -o yogya_analysis.wmv

