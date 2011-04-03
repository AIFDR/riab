./riab/bin/clean.sh
tomcat/bin/catalina.sh start
django-admin.py syncdb --noinput
cd riab_geonode/riab
./manage.py test
tomcat/bin/catalina.sh stop
