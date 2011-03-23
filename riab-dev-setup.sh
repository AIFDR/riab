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
sudo apt-get install -y vim zip unzip subversion git-core binutils build-essential python-dev python-setuptools python-imaging python-reportlab gdal-bin libproj-dev libgeos-dev python-urlgrabber python-scipy python-nose pep8 python-virtualenv python-numpy python-scipy

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

# Get riab source code
checkup AIFDR/riab.git riab
checkup AIFDR/riab_geonode.git riab_geonode
checkup AIFDR/riab_server.git riab_server

virtualenv riab_env
#FIXME: This line is not idempotent, but harmless
echo 'export DJANGO_SETTINGS_MODULE=riab.settings' >> riab_env/bin/activate
source riab_env/bin/activate

# Install GeoNode and it's pre-requisites
wget -c http://203.77.224.75/riab/geonode-webapp.pybundle
wget -c http://203.77.224.75/riab/tomcat-redist.tar.gz
pip install geonode-webapp.pybundle
tar xzf tomcat-redist.tar.gz

python riab_server/setup.py develop
python riab_geonode/setup.py develop

# Reload apache to pickup the project changes
#sudo /etc/init.d/apache2 reload
