tomcat/bin/catalina.sh start
source riab-env/bin/activate
paster serve --reload riab_geonode/riab/deploy/project.paste.ini
deactivate
tomcat/bin/catalina.sh stop
