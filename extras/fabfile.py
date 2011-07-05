from fabric.api import run, sudo, put, env
from fabric.contrib.files import upload_template

# Edit this section if you get tired of writing the parameters on the command line
#env.hosts = ['username@192.168.0.2']
#env.password = 'hardtoremember'


def install():
    """Install RISIKO and it's dependencies
    """
    run('wget https://github.com/AIFDR/riab/raw/master/scripts/risiko-install')
    run('bash risiko-install')
    run('echo "risiko-activate" >> .bash_aliases')


def production():
    """Install and configure Apache and Tomcat
    """
    ctx = dict(user=env.user, host=env.host, riab_home='/home/%s' % env.user)
    upload_template('local_settings.py', 'riab/risiko', context=ctx )
    upload_template('risiko.apache', 'risiko.apache', context=ctx)
    upload_template('tomcat6', 'tomcat6', context=ctx)
    sudo('apt-get install -y libapache2-mod-wsgi')
    sudo('/bin/mv -f risiko.apache /etc/apache2/sites-available/risiko')
    sudo('a2dissite default')
    sudo('a2ensite risiko')
    sudo('a2enmod proxy_http')
    run('mkdir -p logs')
    run('. riab_env/bin/activate; django-admin.py collectstatic --noinput')
    sudo('/bin/mv -f tomcat6 /etc/init.d/')
    sudo('chmod +x /etc/init.d/tomcat6')
    sudo('ln -sf /etc/init.d/tomcat6 /etc/rc1.d/K99tomcat')
    sudo('ln -sf /etc/init.d/tomcat6 /etc/rc2.d/S99tomcat')
    clean()  # Just in case we are installing on top of an existing server
    start()

def manual():
    """Manual steps, not everything can be automated, but we try.
    """

    print "Please perform the following manual steps"
    print
    # Step 1
    print "Step 1. Set up the geoserver proxy url setting to point to the apache frontend proxy"
    print "        if you don't, you will get errors when calling /api/v1/layers"
    print "        Navigate to http://%s/geoserver-geonode-dev/" % env.host
    print "        and click on 'Global Settings', the fill the 'Proxy Base URL' setting with"
    print "        the same path you used to access geoserver (be default geoserver uses http://localhost:8001"

def demo():
    """Install the demo data
    """
    run('. riab_env/bin/activate; risiko-upload risiko_demo_data')

def risiko():
    """Do a full production setup of RISIKO
    """

    install()
    production()
    manual()

def stop():
    """Stop risiko
    """

    sudo('service tomcat6 stop')
    sudo('service apache2 stop')
    sudo('source riab_env/bin/activate;risiko-stop')

def start():
    """Start risiko
    """

    run('source riab_env/bin/activate;django-admin.py syncdb --noinput')
    sudo('service tomcat6 start')
    sudo('service apache2 start')


def refresh():

    clean()
    run('touch riab/extras/project.wsgi')


def pull():
    """Pull the latest changes of the codebase from github and reload the server
    """

    run('cd riab; git pull')
    run('cd geonode; git pull')
    refresh()


def log():
    """Handy way to check the logs
    """
    GEOSERVER_LOG = 'tomcat/webapps/geoserver-geonode-dev/data/logs/geoserver.log'
    run('tail logs/*')
    run('tail -n 50 %s' % GEOSERVER_LOG)
#    run('grep GEONODE_BASE_URL %s' % GEOSERVER_LOG)

def clean():
    """Deletes all the risiko data in the production server.
    """

    stop()
    run('source riab_env/bin/activate; risiko-clean')
    start()


def trash():
    """Destroys all the information and code in your production server.

       In other words, it does the opposite of the install command,
       but leaving the debian packages intact.
    """
    try:
        stop()
        run('source riab_env/bin/activate; risiko-clean')
    except:
        # There is no problem if nothing was running
        pass
    sudo('rm -f /etc/init.d/tomcat*')
    run('rm -f .bash_aliases')
    # Delete home directory
    run('rm -rf ~/*')
    run('rm -f /etc/apachei2/sites-available/risiko')
    sudo('rm -f /etc/rc1.d/K99tomcat')
    sudo('rm -f /etc/rc2.d/S99tomcat')


def local_sources_mirror(country):
    """Create sources with local mirror
    """

    put('%s.sources.list' % country, 'sources.list')
    sudo('/bin/mv -f sources.list /etc/apt')
    sudo('apt-get update')

try:
    from local_fabfile import *
except:
    pass
