#!/bin/bash

./riab/bin/stop_geoserver.py
rm -rf tomcat/webapps/geoserver-geonode-dev
rm -rf tomcat/webapps/geonetwork
rm -f riab_geonode/riab/development.db
