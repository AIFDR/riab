#! /bin/bash

sudo apt-get -y update

#export DEBIAN_FRONTEND=noninteractive
# For Java 6 JDK
#sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
# For GeoNode
#sudo add-apt-repository "deb http://apt.opengeo.org/lucid lucid main"
#sudo apt-get -y update
 # 'Accept' SunOracle Licensing
#sudo echo "sun-java6-bin shared/accepted-sun-dlj-v1-1 boolean true" | sudo debconf-set-selections
#sudo echo "sun-java6-jdk shared/accepted-sun-dlj-v1-1 boolean true" | sudo debconf-set-selections
#sudo echo "sun-java6-jre shared/accepted-sun-dlj-v1-1 boolean true" | sudo debconf-set-selections
#sudo echo "sun-java6-jre sun-java6-jre/stopthread boolean true" | sudo debconf-set-selections
#sudo echo "sun-java6-jre sun-java6-jre/jcepolicy note" | sudo debconf-set-selections
#sudo echo "sun-java6-bin shared/present-sun-dlj-v1-1 note" | sudo debconf-set-selections
#sudo echo "sun-java6-jdk shared/present-sun-dlj-v1-1 note" | sudo debconf-set-selections
#sudo echo "sun-java6-jre shared/present-sun-dlj-v1-1 note" | sudo debconf-set-selections
# Recommended, and useful for Ubuntu 10.04
#sudo apt-get install -y --force-yes sun-java6-jdk

# Needed for auto installation in Ubuntu 10.10
sudo apt-get install -y --force-yes openjdk-6-jre-headless

echo ">>> Installing Ubuntu packages"
# Python development prerequisites
sudo apt-get install -y vim zip unzip subversion git-core binutils build-essential python-dev python-setuptools python-imaging python-reportlab gdal-bin libproj-dev libgeos-dev python-urlgrabber python-scipy python-nose pep8 python-virtualenv python-numpy python-scipy python-gdal python-pastescript

function checkup() {
  REPO="$1"
  WORKING_DIR="$2"
  if [ -d "${WORKING_DIR}" ];
  then
      echo "Updating ${WORKING_DIR} from upstream"
      (cd "${WORKING_DIR}" && git pull)
  else
      git clone "git@github.com:${REPO}" "${WORKING_DIR}" || git clone "https://github.com/${REPO}" "${WORKING_DIR}"
  fi
}

echo ">>> Cloning the repositories"
# Get riab source code
checkup dwins/gsconfig.py gsconfig.py
checkup GeoNode/geonode.git geonode
checkup AIFDR/riab.git riab
checkup AIFDR/riab_geonode.git riab_geonode
checkup AIFDR/riab_server.git riab_server

echo ">>> Creating the virtual environment"
if [ -d riab_env ]; then
    echo 'It already exists...'
else
    virtualenv riab_env
    #FIXME: This line is not idempotent, but harmless
    echo 'export DJANGO_SETTINGS_MODULE=riab.settings' >> riab_env/bin/activate
fi

source riab_env/bin/activate

echo ">>> Downloading riab-libs.pybundle and tomcat bundle"
# Install GeoNode and it's pre-requisites
mkdir temp; cd temp
wget -c http://203.77.224.75/riab/riab-libs.pybundle
wget -c http://203.77.224.75/riab/tomcat-redist.tar.gz
pip install riab-libs.pybundle
tar xzf tomcat-redist.tar.gz
mv apache-tomcat-6.0.32 ../tomcat
cd ..

echo ">>> Installing GeoNode and Riab in dev mode"
pip install -e gsconfig.py
pip install -e geonode/src/GeoNodePy
pip install -e riab_server
pip install -e riab_geonode

django-admin.py syncdb --noinput

echo ""
echo ">>> Running the test suite"
cd riab_server
. run_tests.sh
cd ..

echo ""
echo "Congratulations, you have installed Risk in a Box"
echo "You may want to create a superuser to administer Risk in a Box as follows"
echo "python django-admin.py createsuperuser"
echo
echo "To start the server run the following command:"
echo ""
echo ". riab/startup.sh"
