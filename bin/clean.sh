#!/bin/bash

./riab/bin/stop_all.py
rm -rf tomcat/webapps/geoserver-geonode-dev
rm -rf tomcat/webapps/geonetwork
rm -f riab_geonode/riab/development.db
