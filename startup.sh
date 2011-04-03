tomcat/bin/catalina.sh start
django-admin.py syncdb --noinput
paster serve --reload riab_geonode/riab/deploy/project.paste.ini
tomcat/bin/catalina.sh stop
