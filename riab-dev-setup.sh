#export HOST="127.0.0.1"

export DEBIAN_FRONTEND=noninteractive

sudo apt-get -y dist-upgrade

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
sudo apt-get install -y zip unzip subversion git-core binutils build-essential python-dev python-setuptools python-imaging python-reportlab gdal-bin libproj-dev libgeos-dev python-urlgrabber

sudo echo "geonode geonode/django_user string admin" | sudo debconf-set-selections
sudo echo "geonode geonode/django_password password adm1n" | sudo debconf-set-selections
sudo echo "geonode geonode/hostname string $HOST" | sudo debconf-set-selections
sudo apt-get install -y --force-yes geonode

# Set the owner of GeoNode's virtualenv to be your user (ubuntu in this case)
sudo chown -R ubuntu:ubuntu /var/www/geonode/wsgi/geonode*
echo "source /var/www/geonode/wsgi/geonode/bin/activate" >> ~/.bash_aliases
source /var/www/geonode/wsgi/geonode/bin/activate

# Get riab source code
mkdir -p work;cd work
git clone https://github.com/riab/django-riab.git
git clone https://github.com/riab/riab-client.git
git clone https://github.com/AIFDR/riab_core.git

# Install riab_core
cd riab_core
python setup.py develop
cd ..

# Install django-riab (this will create a symlink in the virtualenv to your working dir)
cd django-riab
python setup.py develop
cd ..

# Compile the javascript sources (minify, etc)
cd ~/work/riab-client
git submodule update --init
sudo apt-get install -y --no-install-recommends ant
export JAVA_HOME=/usr/lib/jvm/java-6-sun
ant zip
# The zipped media dir would end in:
# ~/work/riab-client/build/geonode-client.zip

# Make the server use the djriab project instead of geonode
sudo perl -pi -e 's/geonode.settings/djriab.settings/g' /var/www/geonode/wsgi/geonode.wsgi

# Move the local_settings.py to the right place
mv /var/www/geonode/wsgi/geonode/src/GeoNodePy/geonode/local_settings.py ~/work/django-riab/djriab/

# Reload apache to pickup the project changes
sudo /etc/init.d/apache2 reload

# Install test requirements
#cd ~/work/django-riab
#pip install -r tests/requirements.txt

#python setup.py test
#cd tests
#python manage.py test

#cd ~/work/riab_core
#python setup.py nosetests
#pep8 -v riab_core