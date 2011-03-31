from fabric.api import run, sudo, put, env

# Edit this section if you get tired of writing the parameters on the command line
#env.hosts = ['username@192.168.0.2']
#env.password = 'hardtoremember'

def install():
    """Install RISIKO and it's dependencies
    """
    sudo('apt-get install -y curl')
    run('curl https://github.com/AIFDR/riab/raw/master/install.sh | bash')
    put('bash_aliases', '.bash_aliases')


def production():
    """Install and configure Apache and Tomcat
    """
    put('local_settings.py', 'riab_geonode/riab/')
    sudo('apt-get install -y libapache2-mod-wsgi')
    put('risiko.apache', 'risiko.apache')
    sudo('/bin/mv -f risiko.apache /etc/apache2/sites-available/risiko')
    sudo('a2dissite default')
    sudo('a2ensite risiko')
    sudo('a2enmod proxy_http')
    run('mkdir -p logs')
    sudo('service apache2 restart')
    #FIXME: The staticfiles version we ship is wrong,
    # we need to drop it when we switch to django 1.3
    #run('django-admin.py collectstatic --noinput')
    run('. riab_env/bin/activate; pip install -U django-staticfiles==0.3')
    run('. riab_env/bin/activate; django-admin.py build_static --noinput')
    put('tomcat6', 'tomcat6')
    sudo('/bin/mv -f tomcat6 /etc/init.d/')
    sudo('chmod +x /etc/init.d/tomcat6')
    sudo('service tomcat6 restart')
    sudo('ln -sf /etc/init.d/tomcat6 /etc/rc1.d/K99tomcat')
    sudo('ln -sf /etc/init.d/tomcat6 /etc/rc2.d/S99tomcat')


def manual():
    """Manual steps, not everything can be automated, but we try.
    """

    print "Please perform the following manual steps"
    print
    # Step 1
    print "Step 1. Set up the geoserver proxy url setting to point to the apache frontend proxy"
    print "        if you don't, you will get errors when calling /riab/api/v1/layers"
    print "        Navigate to http://%s/geoserver-geonode-dev/" % env.host
    print "        and click on 'Global Settings', the fill the 'Proxy Base URL' setting with"
    print "        the same path you used to access geoserver (be default geoserver uses http://localhost:8001"
    # Step 2
    print
    print "Step 2. Create a superuser to administer Risk in a Box"
    print "        ssh into the production server and run:"
    print "        django-admin.py createsuperuser"


def test():
    """Run the tests
    """
    run('cd riab_server; ./test_all.sh')


def risiko():
    """Do a full production setup of RISIKO
    """
    install()
    production()
    manual()
    test()


def pull():
    """
    Pull the latest changes of the codebase from github and reload the server
    """

    run('cd riab; git pull')
    run('cd geonode; git pull')
    run('cd riab_server; git pull')
    run('cd riab_geonode; git pull')
    run('touch riab_geonode/riab/deploy/project.wsgi')


def log():
    """Handy way to check the logs
    """

    run('tail logs/*')


def local_sources_mirror(country):
    """Create sources with local mirror
    """

    put('%s.sources.list' % country, 'sources.list')
    sudo('/bin/mv -f sources.list /etc/apt')
    sudo('apt-get update')
