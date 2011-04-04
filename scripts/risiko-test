./riab/bin/clean.sh
tomcat/bin/catalina.sh start
django-admin.py syncdb --noinput
paster serve --reload riab_geonode/riab/deploy/project.paste.ini &
cd riab_geonode/riab
./manage.py test calculations --verbosity=2 --failfast
cd ../../
django-admin.py loaddata riab/bin/users.json
#./stop_all.py
