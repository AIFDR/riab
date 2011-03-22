#export HOST="127.0.0.1"

export DEBIAN_FRONTEND=noninteractive

#sudo apt-get -y dist-upgrade  # This seems to pull in all sorts of stuff like Samba
sudo apt-get update

# For Java 6 JDK
sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"

# For GeoNode
sudo add-apt-repository "deb http://apt.opengeo.org/lucid lucid main"

sudo apt-get -y update
 # 'Accept' SunOracle Licensing
sudo echo "sun-java6-bin shared/accepted-sun-dlj-v1-1 boolean true" | sudo debconf-set-selections
sudo echo "sun-java6-jdk shared/accepted-sun-dlj-v1-1 boolean true" | sudo debconf-set-selections
sudo echo "sun-java6-jre shared/accepted-sun-dlj-v1-1 boolean true" | sudo debconf-set-selections
sudo echo "sun-java6-jre sun-java6-jre/stopthread boolean true" | sudo debconf-set-selections
sudo echo "sun-java6-jre sun-java6-jre/jcepolicy note" | sudo debconf-set-selections
sudo echo "sun-java6-bin shared/present-sun-dlj-v1-1 note" | sudo debconf-set-selections
sudo echo "sun-java6-jdk shared/present-sun-dlj-v1-1 note" | sudo debconf-set-selections
sudo echo "sun-java6-jre shared/present-sun-dlj-v1-1 note" | sudo debconf-set-selections
sudo apt-get install -y --force-yes sun-java6-jdk

# Python development prerequisites
sudo apt-get install -y vim zip unzip subversion git-core binutils build-essential python-dev python-setuptools python-imaging python-reportlab gdal-bin libproj-dev libgeos-dev python-urlgrabber python-scipy python-nose pep8 python-virtualenv

# Get riab source code
git clone git@github.com:AIFDR/riab.git || git clone https://github.com/AIFDR/riab.git
git clone git@github.com:AIFDR/riab_geonode.git || git clone https://github.com/AIFDR/riab_geonode.git
git clone git@github.com:AIFDR/riab_server.git || git clone https://github.com/AIFDR/riab_server.git
git clone git@github.com:geonode/geonode.git || git clone https://github.com/geonode/geonode.git

# Install riab_core
#cd riab_core
#python setup.py develop
#cd ..

# Install django-riab (this will create a symlink in the virtualenv to your working dir)
#cd django-riab
#python setup.py develop
#cd ..

# Compile the javascript sources (minify, etc)
#cd ~/work/riab-client
#git submodule update --init
#sudo apt-get install -y --no-install-recommends ant
#export JAVA_HOME=/usr/lib/jvm/java-6-sun
#ant zip

# The zipped media dir would end in:
# ~/work/riab-client/build/geonode-client.zip

# Make the server use the djriab project instead of geonode
#sudo perl -pi -e 's/geonode.settings/djriab.settings/g' /var/www/geonode/wsgi/geonode.wsgi

# Move the local_settings.py to the right place
#mv /var/www/geonode/wsgi/geonode/src/GeoNodePy/geonode/local_settings.py ~/work/django-riab/djriab/

# Reload apache to pickup the project changes
#sudo /etc/init.d/apache2 reload

# Install test requirements
#cd ~/work/django-riab
#pip install -r tests/requirements.txt

#python setup.py test
#cd tests
#python manage.py test

#cd ~/work/riab_core
#python setup.py nosetests
#pep8 -v riab_core
